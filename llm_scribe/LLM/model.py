import os
from langchain_community.chat_models.moonshot import MoonshotChat

api_key = os.getenv("MOONSHOT_API_KEY")
if not api_key:
    raise RuntimeError("Missing MOONSHOT_API_KEY environment variable")

os.environ["MOONSHOT_API_KEY"] = api_key

model = MoonshotChat(
    model="moonshot-v1-32k",
    temperature=0.3,
    max_tokens=1200,
)
