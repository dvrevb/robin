import gradio as gr
from robin import Robin


async def setup():
    robin = Robin()
    await robin.setup()
    return robin


async def process_message(robin, message, success_criteria, history):
    results = await robin.run_superstep(message, success_criteria, history)
    return results, "", robin  # clear message input after submit


async def reset():
    new_robin = Robin()
    await new_robin.setup()
    return "", "", [], new_robin  # [] instead of None for chatbot


def free_resources(robin):
    print("Cleaning up")
    try:
        if robin:
            robin.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Robin") as ui:
    gr.Markdown("## Robin Personal Co-Worker")
    robin = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Robin", height=300)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Robin")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success criteria?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, outputs=[robin])

    # shared trigger logic
    submit_args = dict(
        fn=process_message,
        inputs=[robin, message, success_criteria, chatbot],
        outputs=[chatbot, message, robin],  # message clears after submit
    )

    message.submit(**submit_args)
    success_criteria.submit(**submit_args)
    go_button.click(**submit_args)

    reset_button.click(reset, [], [message, success_criteria, chatbot, robin])


ui.launch(inbrowser=True)