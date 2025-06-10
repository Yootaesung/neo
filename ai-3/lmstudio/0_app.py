from openai import OpenAI

LM_STUDIO_SERVER_URL = "http://localhost:1234/v1"
client = OpenAI(base_url=LM_STUDIO_SERVER_URL, api_key="lm-studio")

model_name = "llama-3.2-1b-instruct"  # lms ls에서 확인한 로드된 모델 이름

try:
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {'role': 'system', 'content': 'You are a helpful AI assistant.'},
            {'role': 'user', 'content': 'What is the meaning of life?'}
        ],
        temperature=0.7,
        max_tokens=100
    )

    print(completion.choices[0].message.content)

except Exception as e:
    print(f"An error occurred: {e}")
    print('Please check the LM Studio server is running, accessible at the specified url, and a model is loaded.')
