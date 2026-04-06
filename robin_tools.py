import os
import asyncio
import requests

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, Playwright
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit, FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool


load_dotenv(override=True)


PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
SANDBOX_DIR = "sandbox"


serper = GoogleSerperAPIWrapper()


async def playwright_tools() -> tuple[list, Browser, Playwright]:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


async def push(text: str) -> str:
    """Send a push notification via Pushover."""
    response = await asyncio.to_thread(
        requests.post,
        PUSHOVER_URL,
        data={"token": PUSHOVER_TOKEN, "user": PUSHOVER_USER, "message": text},
        timeout=10,
    )
    response.raise_for_status()
    return "success"


def get_file_tools() -> list:
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    toolkit = FileManagementToolkit(root_dir=SANDBOX_DIR)
    return toolkit.get_tools()


async def other_tools() -> list:
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Send a push notification to the user's phone. Use this to alert the user about important results, task completions, or anything that requires their immediate attention.",
    )

    search_tool = Tool(
        name="search",
        func=serper.run,
        description="Search the web for current, real-time, or up-to-date information. Use this for recent events, facts, prices, news, or anything that may not be in your training data.",
    )

    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_repl = PythonREPLTool()
    file_tools = get_file_tools()

    return file_tools + [push_tool, search_tool, python_repl, wiki_tool]