from enum import StrEnum
from typing import List

import structlog
from anthropic import AsyncAnthropic, NOT_GIVEN

import db.kv
from realm.anthropic.models import AnthropicConversationMessage, AnthropicMessageAuthorRole

# Must be < than model's max_tokens().
# Note that streaming is required when max_tokens is greater than 21,333.
# For thinking budgets above 32K: We recommend using batch processing.
# https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking
THINKING_TOKENS_BUDGET = 16_000

_CLIENT: AsyncAnthropic

logger = structlog.get_logger()


class AnthropicModel(StrEnum):
    """
    Defines Anthropic models supported by this bot.
    """

    # Taken from https://docs.anthropic.com/en/docs/about-claude/models
    CLAUDE_3_7_SONNET_LATEST = "claude-3-7-sonnet-latest"
    CLAUDE_SONNET_4_LATEST = "claude-sonnet-4-20250514"

    def max_tokens(self) -> int:
        if self == AnthropicModel.CLAUDE_3_7_SONNET_LATEST:
            # The number of tokens Claude can use for internal reasoning.
            # https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking
            #
            # Normally the model has 8192 max tokens, but we use the extended thinking so need to specify
            # this param to allow tweaking `budget_tokens`.
            # Max value is 64_000
            return 20_000
        elif self == AnthropicModel.CLAUDE_SONNET_4_LATEST:
            # Same as in 3.7
            return 20_000
        else:
            raise ValueError(f"max_tokens: unknown model: {self}")


async def init():
    api_key = await db.kv.get_value(db.kv.Keys.bydlan_anthropic_api_key)
    global _CLIENT
    _CLIENT = AsyncAnthropic(api_key=api_key)


async def create_completion(model: AnthropicModel, system_prompt: str,
                            messages: List[AnthropicConversationMessage]) -> AnthropicConversationMessage:
    """
    See https://docs.anthropic.com/en/api/messages for API reference
    and https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking for thinking reasoning
    """
    # Check how it goes without thinking
    # thinking = {
    #     "type": "enabled",
    #     "budget_tokens": THINKING_TOKENS_BUDGET,
    # }
    thinking = NOT_GIVEN
    serialized_messages = [m.dict() for m in messages]
    response = await _CLIENT.messages.create(
        model=model,
        max_tokens=model.max_tokens(),
        system=system_prompt,
        messages=serialized_messages,
        thinking=thinking,
        # tools=[{
        #     "type": "web_search_20250305",
        #     "name": "web_search",
        #     "max_uses": 5,
        # }]
    )
    result = AnthropicConversationMessage(role=AnthropicMessageAuthorRole.assistant, content=response.content)
    return result
