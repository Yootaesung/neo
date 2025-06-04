class Message:
    def __init__(self, content: str):
        self.text = content

class UserMessage(Message):
    pass

class AssistantMessage(Message):
    pass