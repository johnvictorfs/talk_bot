import asyncio
import random

import discord

from talk_bot.orm.models import Message


def make_pairs(data):
    for i in range(len(data) - 1):
        yield (data[i], data[i + 1])


def get_words() -> list:
    """
    Gets the message content of all messages stored in the bot's database and returns a list
    of all individual words in those messages
    """
    messages = Message.select()
    all_words = [m.content.split(' ') for m in messages]
    return [word for message in all_words for word in message]


def make_phrase(size: int = 30) -> str:
    words = get_words()
    pairs = make_pairs(words)
    word_dict = {}
    for word_1, word_2 in pairs:
        if word_1 in word_dict.keys():
            word_dict[word_1].append(word_2)
        else:
            word_dict[word_1] = [word_2]
    chain = [random.choice(words)]
    for i in range(size):
        chain.append(random.choice(word_dict[chain[-1]]))
    return ' '.join(chain)


async def send_messages(channel: discord.TextChannel, delay: int = 5, size: int = 30):
    while True:
        message = make_phrase(size)
        await channel.send(message)
        await asyncio.sleep(60 * delay)
