import os
from langchain_community.chat_models.moonshot import MoonshotChat

key = "sk-oYmzIcdwWOG8YMLkpcYTtj3sVsmkmQkCnBC1mNBTUqjXJI5k"

os.environ["MOONSHOT_API_KEY"] = key

model = MoonshotChat(
    model="moonshot-v1-32k",
    temperature=0.3,
    max_tokens=1200,
)
