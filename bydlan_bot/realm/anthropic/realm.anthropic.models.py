import typing
from enum import Enum

import anthropic.types
from pydantic import BaseModel


class AnthropicMessageAuthorRole(str, Enum):
    """
    Defines message author role to allow Anthropic to distinguish between user's and its own messages.
    See https://docs.anthropic.com/en/api/messages for values
    """
    user = "user"
    assistant = "assistant"


class AnthropicConversationMessage(BaseModel):
    """
    Defines a message used in a conversation with Anthropic.
    Field names are taken from https://docs.anthropic.com/en/api/messages
    """
    role: AnthropicMessageAuthorRole
    content: typing.List[anthropic.types.ContentBlock]

    @classmethod
    def from_group_chat_text(cls, author_first_name: typing.Optional[str],
                             user_text: str) -> "AnthropicConversationMessage":
        if author_first_name:
            text = f"{author_first_name}: {user_text}"
        else:
            text = user_text
        content_block = anthropic.types.TextBlock(type="text", text=text)
        return cls(role=AnthropicMessageAuthorRole.user, content=[content_block])

    @classmethod
    def from_group_chat_bot_text(cls, bot_text: str) -> "AnthropicConversationMessage":
        content_block = anthropic.types.TextBlock(type="text", text=bot_text)
        return cls(role=AnthropicMessageAuthorRole.assistant, content=[content_block])

    @classmethod
    def dummy_bot_message(cls) -> "AnthropicConversationMessage":
        content_block = anthropic.types.TextBlock(type="text", text="лолкек")
        return cls(role=AnthropicMessageAuthorRole.assistant, content=[content_block])

    def assistant_text_blocks(self) -> typing.List[str]:
        """
        Returns the assistant text (while skipping thinking entries), basically returns the first text block of
        the response.
        """
        text_blocks = [block.text for block in self.content if isinstance(block, anthropic.types.TextBlock)]
        if len(text_blocks) == 0:
            return ["<assistant text not found in response>"]
        else:
            return text_blocks
