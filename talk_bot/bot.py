from pathlib import Path
import sys
import json
import asyncio
import logging
import datetime

import discord
from discord.ext import commands

from talk_bot.orm.models import db, Message, IgnoredChannel


def load_settings() -> dict:
    """
    Loads bot settings from 'settings.json' file

    Example settings file at 'settings.example.json'
    """
    with open('settings.json', 'r') as f:
        return json.load(f)


class Bot(commands.Bot):
    def __init__(self, settings: dict):
        super().__init__(command_prefix=settings.get('prefix'), case_insensitive=True)
        self.settings = settings
        self.start_time = None
        self.app_info = None

        self.db_setup()
        self.remove_command('help')
        self.loop.create_task(self.track_start())
        self.loop.create_task(self.load_all_extensions())

    async def track_start(self):
        """
        Waits for the bot to connect to discord and then records the time
        """
        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

    async def load_all_extensions(self):
        """
        Attempts to load all .py files in /cogs/ as cog extensions
        """
        await self.wait_until_ready()
        await asyncio.sleep(1)  # ensure that on_ready has completed and finished printing
        disabled = ['__init__']
        cogs = [x.stem for x in Path('cogs').glob('*.py')]
        cogs = [c for c in cogs if c not in disabled]
        for extension in cogs:
            try:
                self.load_extension(f'cogs.{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'Failed to load extension {error}')
            print('-' * 10)

    async def on_ready(self):
        """
        This event is called every time the bot connects or resumes connection.
        """
        print('-' * 10)
        self.app_info = await self.application_info()
        print(f'Logged in as: {self.user.name}\n'
              f'Using discord.py version: {discord.__version__}\n'
              f'Owner: {self.app_info.owner}\n'
              f'Prefix: {self.settings.get("prefix")}\n'
              f'Template Maker: SourSpoon / Spoon#7805')
        print('-' * 10)

    async def on_message(self, message: discord.Message):
        """
        This event triggers on every message received by the bot
        """
        if message.author.bot:
            return  # Ignore all bot messages
        self.add_message(message)
        await self.process_commands(message)

    def add_message(self, message: discord.Message):
        """
        Adds message details to database if:
            - It wasn't sent in an ignored channel
            - If it doesn't start with the bot's command prefix
            - If it doesn't have less than 10 characters
        """
        if len(message.content) < 10:
            return
        is_command = message.content.startswith(self.settings.get('prefix'))
        if is_command:
            return
        is_ignored = IgnoredChannel.select().where(IgnoredChannel.channel_id == message.channel.id)
        if is_ignored:
            return
        if not is_ignored:
            Message.create(
                content=message.content,
                author_name=message.author.name,
                author_id=message.author.id,
                channel_id=message.channel.id,
                timestamp=message.created_at
            )

    @staticmethod
    def db_setup():
        """
        Setups the bot's database, creates necessary tables if not yet created
        """
        db.connect()
        db.create_tables([Message, IgnoredChannel])
        db.close()


async def run(settings: dict):
    bot = Bot(settings=settings)
    try:
        await bot.start(settings.get('token'))
    except KeyboardInterrupt:
        await bot.logout()
    except discord.errors.LoginFailure:
        print(f"Error: Invalid Token. Please input a valid token in '/talk_bot/settings.json' file.")
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(settings=load_settings()))
