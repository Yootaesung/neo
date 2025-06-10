import ollama

response = ollama.chat(
    model="llama3.2:latest",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Code a Python function to generate a Fibonacci sequence."}
    ]
)

print(response)