import gradio as gr
from transformers import pipeline
pipe = pipeline("image-classification")
gr.Interface.from_pipeline(pipe).launch()