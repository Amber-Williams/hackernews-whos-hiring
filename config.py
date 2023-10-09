from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MONTH: str = "october"
    YEAR: str = "2023"

settings = Settings()