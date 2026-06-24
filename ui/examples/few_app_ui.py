import gradio as gr

# 1. Первое приложение - переводчик
def translate_to_english(text):
    translations = {"привет": "hello", "мир": "world", "кот": "cat"}
    return translations.get(text.lower(), "Неизвестное слово")

translator_app = gr.Interface(
    fn=translate_to_english,
    inputs=gr.Textbox(label="Русское слово"),
    outputs=gr.Textbox(label="Английский перевод"),
    title="Переводчик"
)

# 2. Второе приложение - загрузка переводчика
with gr.Blocks() as demo:
    gr.Markdown("# Мой мультиязычный помощник")
    

    # Загружаем переводчик
    loaded_translator = gr.Interface.load(
        translator_app
    )

    
    # Добавляем свой функционал
    with gr.Row():
        gr.Markdown("### Дополнительные функции")
        
    with gr.Row():
        btn = gr.Button("Показать справку")
        output = gr.Textbox()
        
        def show_help():
            return "Используйте переводчик выше для перевода слов"
        
        btn.click(show_help, outputs=output)

demo.launch()