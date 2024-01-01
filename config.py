
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL') or "gpt-3.5-turbo-1106"
    MONTH: str = os.getenv('MONTH')
    YEAR: str = os.getenv('YEAR')
    TOKEN_LIMIT: int = os.getenv('TOKEN_LIMIT') or 4096

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    if not MONTH:
        raise ValueError("MONTH not found in .env file")
    if not YEAR:
        raise ValueError("YEAR not found in .env file")


settings = Settings()