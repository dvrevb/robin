from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from robin_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Robin:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.robin_id = str(uuid.uuid4())
        self.browser = None
        self.playwright = None

    async def setup(self):
        self._db_conn = await aiosqlite.connect("RobinMemory.db")
        self.memory = AsyncSqliteSaver(self._db_conn)
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a capable and autonomous assistant that uses tools to complete tasks end-to-end.
    You keep working until you either need clarification from the user, or the success criteria is fully met.

    You have access to the following tools:
    - Browser tools: navigate and retrieve web pages, click, fill forms, take screenshots
    - Web search: for current, real-time, or recent information
    - Wikipedia: for encyclopedic, well-established background knowledge
    - Python REPL: execute Python code; always use print() to see output
    - File tools: read and write files to the sandbox directory
    - Push notification: alert the user when a task is done or something needs their attention

    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is the success criteria you must meet:
    {state["success_criteria"]}

    Reply with either:
    - A question for the user if you need clarification to proceed. Start it clearly with "Question:" for example:
    Question: Should I summarize the results or provide the full details?
    - Your final answer once the task is complete. Do not add unnecessary questions at the end.
    """
        if state.get("feedback_on_work"):
            system_message += f"""
    You previously attempted this task but your response did not meet the success criteria.
    Here is the feedback explaining why it was rejected:
        {state["feedback_on_work"]}

    Review this feedback carefully and continue working to fully satisfy the success criteria.
    Do not repeat the same approach if it was already rejected. Try a different strategy if needed.
    """

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are a strict evaluator that determines whether an Assistant has fully completed a task.
    Your job is to assess quality, accuracy, and completeness — not just whether the Assistant attempted the task.
    Be critical: partial answers, vague responses, or incomplete work should not be marked as success.
    The Assistant has access to the internet, so do not penalize it for lacking up-to-date information — it can and should look things up."""

        user_message = f"""You are evaluating a conversation between a User and an Assistant.

    Full conversation:
    {self.format_conversation(state["messages"])}

    Success criteria:
    {state["success_criteria"]}

    Assistant's final response:
    {last_response}

    Evaluate the response and decide:
    1. Does it fully satisfy the success criteria? Be strict — partial or vague answers should fail.
    2. Is user input needed? Set this to True if:
        - The assistant is asking the user a question
        - The assistant is stuck or repeating itself
        - Clarification is genuinely required to proceed

    Notes:
        - If the Assistant says they wrote a file, trust that they did.
        - If the Assistant says they sent a push notification, trust that they did.
        - Do not pass a response just because the assistant tried hard — the criteria must actually be met.
    """
        if state["feedback_on_work"]:
            user_message += f"\nIn a prior attempt you gave this feedback: {state['feedback_on_work']}\n"
            user_message += "If the Assistant is repeating the same mistakes or not improving, set user_input_needed to True.\n"


        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.robin_id}}

        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        try:
            loop = asyncio.get_running_loop()
            if self._db_conn:
                loop.create_task(self._db_conn.close())
            if self.browser:
                loop.create_task(self.browser.close())
            if self.playwright:
                loop.create_task(self.playwright.stop())
        except RuntimeError:
            if self._db_conn:
                asyncio.run(self._db_conn.close())
            if self.browser:
                asyncio.run(self.browser.close())
            if self.playwright:
                asyncio.run(self.playwright.stop())
