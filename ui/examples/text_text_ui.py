import gradio as gr

def reverse(text):
    return text[::-1]

demo = gr.Interface(reverse, "text", "text")
demo.queue()
demo.launch(share=True, auth=("username", "password"))