import os
from llm_scribe.config import settings
# LangChain ChatModel
from langchain_openai import ChatOpenAI  # OpenAI / DeepSeek / Qwen / GLM
from langchain_community.chat_models.moonshot import MoonshotChat
from langchain_community.chat_models import ChatOllama

# Claude
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

# Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

def safe_env_set(key: str, value):
    if value is not None and str(value).strip() != "":
        os.environ[key] = str(value)

def get_llm():
    """根据 .env 配置返回对应的 LangChain ChatModel 实例"""
    provider = (settings.LLM_PROVIDER or "").lower()

    # Moonshot
    if provider == "moonshot":
        safe_env_set("MOONSHOT_API_KEY", settings.MOONSHOT_API_KEY)
        if not settings.MOONSHOT_API_KEY:
            print("⚠️ [LLM-Scribe] 未设置 MOONSHOT_API_KEY，模型可能无法调用。")
        return MoonshotChat(
            model=settings.MOONSHOT_MODEL,
            base_url=settings.MOONSHOT_BASE_URL,
            temperature=0.3,
            max_tokens=1200,
        )
    # penAI
    if provider == "openai":
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY or "",
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
        )
    # DeepSeek
    if provider == "deepseek":
        return ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY or "",
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL,
        )
    # Qwen
    if provider == "qwen":
        return ChatOpenAI(
            api_key=settings.QWEN_API_KEY or "",
            base_url=settings.QWEN_BASE_URL,
            model=settings.QWEN_MODEL,
        )
    # GLM
    if provider == "glm":
        return ChatOpenAI(
            api_key=settings.GLM_API_KEY or "",
            base_url=settings.GLM_BASE_URL,
            model=settings.GLM_MODEL,
        )
    # Claude
    if provider == "claude":
        if ChatAnthropic is None:
            raise ImportError("请安装: pip install langchain-anthropic")
        return ChatAnthropic(
            api_key=settings.CLAUDE_API_KEY or "",
            model=settings.CLAUDE_MODEL,
            temperature=0.3,
            max_tokens=1200,
        )
    # Gemini
    if provider == "gemini":
        if ChatGoogleGenerativeAI is None:
            raise ImportError("请安装: pip install langchain-google-genai")
        return ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY or "",
            model=settings.GEMINI_MODEL,
            temperature=0.3,
            max_output_tokens=1200,
        )
    # Ollama
    if provider == "ollama":
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    raise ValueError(f"❌ 不支持的模型提供商: {provider}")
