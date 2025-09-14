import typing

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def split_if_large_message(message: str) -> typing.List[str]:
    """
    Splits messages in chunks of size `TELEGRAM_MAX_MESSAGE_LENGTH`
    """
    return [message[i:i + TELEGRAM_MAX_MESSAGE_LENGTH] for i in
            range(0, len(message), TELEGRAM_MAX_MESSAGE_LENGTH)]
