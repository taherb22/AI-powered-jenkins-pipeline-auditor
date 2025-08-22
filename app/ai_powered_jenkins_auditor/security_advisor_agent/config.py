import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found. Please add it to your .env file.")

TEMPERATURE = 0.1
MAX_TOKENS = 4096
class GroqFallbackClient:
    def __init__(self, primary_model, fallback_model):
        self.primary = primary_model
        self.fallback = fallback_model
        self.active_client = self.primary

    def __call__(self, prompt, *args, **kwargs):
        try:
            
            return self.active_client.invoke(prompt, *args, **kwargs)
        except Exception as e:
            if "rate limit" in str(e).lower():
                self.active_client = self.fallback
                return self.active_client.invoke(prompt, *args, **kwargs)
            else:
                raise

    def invoke(self, *args, **kwargs):
        return self.__call__(*args, **kwargs)



primary_client = ChatGroq(model="openai/gpt-oss-120b", api_key=groq_api_key, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
fallback_client = ChatGroq(model="meta-llama/llama-guard-4-12b", api_key=groq_api_key, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)

llm_client = GroqFallbackClient(primary_client, fallback_client)