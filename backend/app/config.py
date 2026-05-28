"""Configuracion de la aplicacion, cargada desde variables de entorno (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # URL base de Ollama
    ollama_base_url: str = "http://localhost:11434"
    # Modelo por defecto
    ollama_model: str = "qwen2.5-coder:7b"
    # Origenes permitidos para CORS (separados por comas)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
