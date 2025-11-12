from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):

    # LLM Provider
    LLM_PROVIDER: str = Field(
        default="moonshot",
        description="选择使用哪种 LLM：moonshot/openai/deepseek/qwen/glm/claude/gemini/ollama"
    )

    # Moonshot
    MOONSHOT_API_KEY: str | None = None
    MOONSHOT_MODEL: str = "moonshot-v1-32k"
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1"

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # DeepSeek
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Qwen (DashScope)
    QWEN_API_KEY: str | None = None
    QWEN_MODEL: str = "qwen-max"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # GLM (Zhipu ChatGLM)
    GLM_API_KEY: str | None = None
    GLM_MODEL: str = "glm-4"
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # Claude
    CLAUDE_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-3-sonnet"
    CLAUDE_BASE_URL: str = "https://api.anthropic.com/v1"

    # Gemini
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    # Ollama (Local)
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # MySQL Database
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "diting_qq_bot"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"

settings = Settings()
