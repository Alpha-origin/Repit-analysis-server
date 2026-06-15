import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    CLAUDE_API_KEY: str = os.getenv("Claude_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    API_SERVER_BASE_URL: str = os.getenv("API_SERVER_BASE_URL", "")
    ANALYSIS_CALLBACK_PATH: str = os.getenv("ANALYSIS_CALLBACK_PATH", "")
    ANALYSIS_CALLBACK_SECRET: str = os.getenv("ANALYSIS_CALLBACK_SECRET", "")


settings = Settings()
