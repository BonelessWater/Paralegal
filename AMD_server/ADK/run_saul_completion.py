# file: run_saul_completion.py
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

resp = client.completions.create(
    model="Equall/Saul-7B-Instruct-v1",
    prompt="Write a one-sentence summary of what gradient descent does.",
    max_tokens=64,
    temperature=0.2,
)
print(resp.choices[0].text)
