import asyncio
import typing

import cachetools
import pyrogram.enums
import structlog
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from db import kv
from realm.anthropic.api import create_completion, AnthropicModel
from realm.anthropic.models import AnthropicConversationMessage
from realm.anthropic.system_prompts import BYDLAN_SYSTEM_PROMPT
from realm.telegram.utils import split_if_large_message
from realm.telegram.myno_debug import send_debug_message

logger = structlog.get_logger()

# Will be set dynamically after bot starts
BYDLAN_USERNAME = None

BYDLAN_PREFIX = "быдлан"

_CLIENT: Client = None
_CONVERSATIONS = cachetools.Cache(maxsize=1000)


async def graceful_shutdown():
    global _CLIENT
    if _CLIENT:
        try:
            await _CLIENT.stop()
            logger.info("Bot stopped gracefully")
        except Exception as e:
            logger.error("Error during shutdown", error=e)


async def init():
    global _CLIENT, BYDLAN_USERNAME
    
    logger.info("Initializing Telegram client...")
    
    # in-memory session will be discarded as soon as the client stops
    client = Client("bydlan", in_memory=True, workers=4)

    # Set secrets
    try:
        client.api_id = int(await kv.get_value(kv.Keys.tg_client_api_id))
        client.api_hash = await kv.get_value(kv.Keys.tg_client_api_hash)
        client.bot_token = await kv.get_value(kv.Keys.tg_bot_token_bydlan)
        
        logger.info("Credentials loaded successfully")
    except Exception as e:
        logger.error("Failed to load credentials", error=e)
        raise

    # Register handlers
    client.add_handler(MessageHandler(handle_group_message, filters=filters.group))

    # Start client, so it's ready to be used
    logger.info("Starting Telegram client...")
    await client.start()
    
    # Get bot info and set username
    try:
        bot_info = await client.get_me()
        BYDLAN_USERNAME = bot_info.username
        logger.info(f"Bot started successfully as @{BYDLAN_USERNAME}")
    except Exception as e:
        logger.error("Failed to get bot info", error=e)
        BYDLAN_USERNAME = "BydlanBot"  # fallback
    
    _CLIENT = client


def get_bydlan() -> Client:
    return _CLIENT


async def send_debug_msg(msg: str):
    """Send debug message - renamed to avoid import conflicts"""
    try:
        reply_messages = split_if_large_message(msg)
        for reply_msg in reply_messages:
            if len(reply_msg) == 0:
                continue
            await send_debug_message(reply_msg)
    except Exception:
        cut = msg[:256]
        await send_debug_message(f"failed to send debug message, go check logs mfer: {cut}")


async def handle_group_message(client: Client, message: Message):
    """
    If a group message is bydlan-reactable:
      1. Go through reply chain to build context
      2. Reply to the message

    It also maintains a conversation history which gets saved on every bydlan response. On the next response, the previous
    conversation gets cleared.
    """
    try:
        if not should_react(message):
            return

        logger.info("Processing message from group", chat_id=message.chat.id)

        # Gather context
        messages = await get_conversation(client, message)

        # Add current message to the context
        # and strip bydlan prefix from it so he doesn't get triggered
        user_name = message.from_user.first_name if message.from_user else "Unknown"
        messages.append(AnthropicConversationMessage.from_group_chat_text(
            user_name, strip_bydlan_prefix(message.text)
        ))

        # Get response from anthropic
        logger.info("Getting response from Claude...")
        bydlan_response = await create_completion(AnthropicModel.CLAUDE_3_7_SONNET_LATEST, BYDLAN_SYSTEM_PROMPT,
                                                  messages)
        messages.append(bydlan_response)
        bydlan_response_text = "".join(bydlan_response.assistant_text_blocks())

        # Send response(s) to the chat
        last_sent_msg = await send_reply(message, bydlan_response_text)

        # and save conversation (with deleting the previous one)
        key = make_cache_key(message.chat.id, message.reply_to_message_id)
        if message.reply_to_message_id and _CONVERSATIONS.get(key):
            del _CONVERSATIONS[key]
        _CONVERSATIONS[make_cache_key(message.chat.id, last_sent_msg.id)] = messages

        logger.info("Message processed successfully")

    except Exception as e:
        logger.error("failed to handle group message", error=e)
        try:
            await message.reply(f"еррор ебана\n\n{e}", reply_to_message_id=message.id)
        except Exception as reply_error:
            logger.error("Failed to send error message", error=reply_error)


def make_cache_key(chat_id, message_id) -> str:
    return f"{chat_id}:{message_id}"


async def get_conversation(client: Client, message: Message) -> typing.List[AnthropicConversationMessage]:
    """
    Either returns a cached conversation (containing bydlan responses) or creates a new one (traversing
    through parent messages if present).
    """
    if message.reply_to_message_id:
        cached_context: typing.List[AnthropicConversationMessage] = _CONVERSATIONS.get(
            make_cache_key(message.chat.id, message.reply_to_message_id))
        if cached_context:
            return cached_context

    # Message was not yet cached, traverse the replies (if any) and cache them
    context = []
    chat_id = message.chat.id
    next_msg_id = message.reply_to_message_id
    logger.info("start iterating over telegram replies")
    while next_msg_id:
        # Get parent and save it to the context
        parent_msg = await client.get_messages(chat_id, message_ids=next_msg_id)
        logger.info("handling parent message", msg=parent_msg)
        # wait for a bit to avoid spamming tg servers
        await asyncio.sleep(0.2)

        if not parent_msg:
            break
        author = parent_msg.from_user
        if not author:
            # this is likely another bot's message
            logger.warning("msg author not found", msg=parent_msg)
            await send_debug_msg(f"msg author not found: {parent_msg}")
            # just in case to avoid spamming
            await asyncio.sleep(0.3)
        elif author.username and author.username == BYDLAN_USERNAME:
            context.append(
                AnthropicConversationMessage.from_group_chat_bot_text(parent_msg.text))
        else:
            if not author.first_name:
                logger.warning("author without a first name", msg=parent_msg)
                await send_debug_msg(f"author without a first name: {parent_msg}")
                # just in case to avoid spamming
                await asyncio.sleep(0.3)

            context.append(
                AnthropicConversationMessage.from_group_chat_text(parent_msg.from_user.first_name, parent_msg.text))

        next_msg_id = parent_msg.reply_to_message_id
    logger.info("finish iterating over telegram replies")

    # reverse the history so the oldest message goes first
    context.reverse()
    return context


def should_react(message: Message) -> bool:
    """
    Returns True when bydlan should react to a message:
        1. if it starts with "быдлан"
        2. if it is a reply to bydlan's message
    """
    if not message.text:
        return False
    if message.text.lower().startswith(BYDLAN_PREFIX):
        return True
    parent_message = message.reply_to_message
    if (parent_message is not None 
        and parent_message.from_user is not None 
        and parent_message.from_user.username is not None 
        and parent_message.from_user.username == BYDLAN_USERNAME):
        return True
    return False


async def send_reply(message: Message, response: str) -> Message:
    reply_messages = split_if_large_message(response)
    last_reply_to_message = message
    reply_to_id = message.id
    for reply_msg in reply_messages:
        if len(reply_msg) == 0:
            continue

        logger.info("sending reply message", message=reply_msg)
        sent_msg = await message.reply(
            reply_msg,
            reply_to_message_id=reply_to_id,
            parse_mode=pyrogram.enums.ParseMode.MARKDOWN,
        )
        reply_to_id = sent_msg.id
        last_reply_to_message = sent_msg
    return last_reply_to_message


def strip_bydlan_prefix(text: str) -> str:
    if text.lower().startswith(BYDLAN_PREFIX):
        # remove the first word (to support cases like быдланчик, etc.)
        return " ".join(text.split(" ")[1:])
    else:
        return text
