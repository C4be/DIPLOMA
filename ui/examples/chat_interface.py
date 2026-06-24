# import gradio as gr

# def echo(message, history):
#     return f'```py\nprint(\'hello world\')\n```'

# demo = gr.ChatInterface(fn=echo, examples=["hello", "hola", "merhaba"], title="Echo Bot")
# demo.launch()


import gradio as gr

def yes(message, history):
    return "yes"

def vote(data: gr.LikeData):
    if data.liked:
        print("You upvoted this response: " + data.value["value"])
    else:
        print("You downvoted this response: " + data.value["value"])

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(placeholder="<strong>Your Personal Yes-Man</strong><br>Ask Me Anything")
    chatbot.like(vote, None, None)
    gr.ChatInterface(fn=yes, chatbot=chatbot)
    
demo.launch()