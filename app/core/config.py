import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    CLAUDE_API_KEY: str = os.getenv("Claude_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
