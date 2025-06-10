from langchain.llms import OpenAI

llm = OpenAI(
    model = 'gpt-3.5-turbo-instruct',
    temperature = 0.9         # 1에 가까우면 창의적, 0에 가까우면
)

print(llm("컴퓨터 게임을 만드는 새로운 회사이름을 하나 제안해주세요."))