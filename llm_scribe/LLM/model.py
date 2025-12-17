from langchain_community.chat_models.moonshot import MoonshotChat

from ..config import get_config

cfg = get_config()
api_key = cfg.moonshot_api_key
if not api_key:
    raise RuntimeError("Missing moonshot_api_key in plugin config / environment")

model = MoonshotChat(
    model="moonshot-v1-32k",
    temperature=0.3,
    max_tokens=1600,
)
