
import os
from datetime import datetime

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL')
    MONTH: str = os.getenv('MONTH') or datetime.now().strftime('%B')
    YEAR: str = os.getenv('YEAR') or datetime.now().strftime('%Y')
    TOKEN_LIMIT: int = os.getenv('TOKEN_LIMIT') or 4096

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    if not OPENAI_MODEL:
        raise ValueError("OPENAI_MODEL not found in .env file")
    if not MONTH:
        raise ValueError("MONTH not found in .env file")
    if not YEAR:
        raise ValueError("YEAR not found in .env file")


settings = Settings()