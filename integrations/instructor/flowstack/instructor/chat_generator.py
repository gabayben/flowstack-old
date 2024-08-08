from flowstack.components.ai.chat_generator import BaseChatGenerator, ChatPrompt
from flowstack.messages import BaseMessage

class InstructorChatGenerator(BaseChatGenerator):
    def _invoke(self, prompt: ChatPrompt, **kwargs) -> BaseMessage:
        pass