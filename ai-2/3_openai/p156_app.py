import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

models = openai.Model.list()

print(models["data"][0]["id"])