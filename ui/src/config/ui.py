import gradio as gr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsUI(BaseSettings):
    make_share: bool
    ui_theme: str

    model_config = SettingsConfigDict(
        env_file="config.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_theme_class(self):
        color = self.ui_theme.lower()
        match color:
            case "citrus":
                return gr.themes.Citrus()
            case "default":
                return gr.themes.Default()
            case "glass":
                return gr.themes.Glass()
            case "monochrome":
                return gr.themes.Monochrome()
            case "ocean":
                return gr.themes.Ocean()
            case "origin":
                return gr.themes.Origin()
            case "soft":
                return gr.themes.Soft()
            case _:
                raise ValueError(f"Неизвестный тип оформления: {color}")


settings_ui = SettingsUI()
