import re
import sys
import json
import asyncio
import logging
import datetime
from pathlib import Path

import discord
from discord.ext import commands

from talk_bot.orm.models import db, Message, IgnoredChannel
from talk_bot.tasks.sender import send_messages


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
        cogs = [x.stem for x in Path('cogs').glob('*.py') if x.stem not in disabled]
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
        try:
            channel = self.get_channel(int(self.settings.get('messages_channel')))
        except (TypeError, ValueError):
            print(f'Error: Invalid messages channel: {self.settings.get("messages_channel")}')
            sys.exit(1)
        try:
            delay = int(self.settings.get('messages_delay'))
        except (TypeError, ValueError):
            print(f'Error: Invalid messages delay: {self.settings.get("messages_delay")}')
            sys.exit(1)
        self.loop.create_task(send_messages(channel, delay))
        await self.populate_db()

    async def on_message(self, message: discord.Message):
        """
        This event triggers on every message received by the bot
        """
        if message.author.bot:
            return  # Ignore all bot messages
        # Only allow messages sent on a guild
        if message.guild:
            self.add_message(message)
        await self.process_commands(message)

    async def send_logs(self, e: Exception, tb: str, ctx: commands.Context = None):
        """
        Sends logs of errors to the bot's instance owner as a private Discord message
        """
        owner = self.app_info.owner
        separator = ("_\\" * 15) + "_"
        info_embed = None
        if ctx:
            info_embed = discord.Embed(title="__Error Info__", color=discord.Color.dark_red())
            info_embed.add_field(name="Message", value=ctx.message.content, inline=False)
            info_embed.add_field(name="By", value=ctx.author, inline=False)
            info_embed.add_field(name="In Guild", value=ctx.guild, inline=False)
            info_embed.add_field(name="In Channel", value=ctx.channel, inline=False)
        try:
            await owner.send(content=f"{separator}\n**{e}:**\n```python\n{tb}```", embed=info_embed)
        except discord.errors.HTTPException:
            logging.error(f"{e}: {tb}")
            try:
                await owner.send(
                    content=f"(Sending first 500 chars of traceback, too long)\n{separator}\n**{e}:**"
                    f"\n```python\n{tb[:500]}```",
                    embed=info_embed
                )
            except Exception:
                await owner.send(content="Error trying to send error logs.", embed=info_embed)

    def clean_db(self):
        """
        Removes all Messages from DB that were sent by a Bot or in a NSFW channel and calls
        Bot.format_message() on the message's content to check for anything else that's wrong

        TODO: Refactor this to be non-blocking, currently blocks the bot for ~3 minutes with 17k messages in the DB
        """
        for message in Message.select():
            channel = self.get_channel(message.channel_id)

            # Deletes message from database if it was sent in a channel that is now ignored
            ignored_channel = Message.select().where(Message.channel_id == channel.id)
            if ignored_channel:
                message.delete()
                continue

            # Deletes message if it was sent in a nsfw channel
            if channel:
                if channel.is_nsfw():
                    Message.delete().where(Message.channel_id == channel.id)
                    continue

            message.content = self.clean_message(message.content, message.channel_id)
            message.save()
            author = self.get_user(message.author_id)

            # Deletes message if it was sent by a bot
            if author:
                if author.bot:
                    Message.delete().where(Message.author_id == author.id)

    def is_valid_message(self, message: discord.Message) -> bool:
        """
        Checks if a message is valid to be put in the bot's database

        The message needs to be:
            - Sent in a not NSFW channel
            - From a non-bot user
            - Have 10 characters or higher
            - Not start with the bot's command prefix
            - Sent in a not ignored channel
        """
        if message.channel.is_nsfw():
            return False
        if message.author.bot:
            return False
        if len(message.content) < 10:
            return False
        command_prefixes = {self.settings.get('prefix'), '!', '?', '+', '.'}
        is_command = (message.content.startswith(prefix) for prefix in command_prefixes)
        if is_command:
            return False
        is_ignored = IgnoredChannel.select().where(IgnoredChannel.channel_id == message.channel.id)
        if is_ignored:
            return False
        return True

    def add_message(self, message: discord.Message):
        """
        Adds message details to database if:
            - If it wasn't sent in a NSFW channel
            - If it wasn't send by a bot
            - It it wasn't sent in an ignored channel
            - If it doesn't start with the bot's command prefix
            - If it doesn't have less than 10 characters
        """
        if self.is_valid_message(message):
            Message.create(
                message_id=message.id,
                content=message.content,
                author_name=message.author.name,
                author_id=message.author.id,
                channel_id=message.channel.id,
                timestamp=message.created_at
            )

    def clean_message(self, content: str, channel_id: int) -> str:
        # Replaces all mentions to other users or roles in messages with just the names of the user
        # the mention was referring to
        # Also wraps @everyone and @here in in-line code so they don't mention anyone
        # Mentions to users are formatted like so: <@546527580715745290>
        # Mentions to roles are formatted like so: <@&546527580715745290>

        user_mentions = re.findall(r'(<@\d+>)', content)
        for mention in user_mentions:
            user_id = re.search(r'\d+', mention)
            user_id = user_id.group()
            user: discord.Member = self.get_user(int(user_id))
            if user:
                content = content.replace(mention, user.display_name)
            else:
                content = content.replace(mention, '')

        role_mentions = re.findall(r'(<@&\d+>)', content)
        for mention in role_mentions:
            role_id = re.search(r'\d+', mention)
            role_id = role_id.group()
            channel: discord.TextChannel = self.get_channel(channel_id)
            guild: discord.Guild = channel.guild
            role: discord.Role = guild.get_role(int(role_id))
            if role:
                content = content.replace(mention, role.name)
            else:
                content = content.replace(mention, '')

        content = content.replace('@everyone', '`@everyone`')
        content = content.replace('@here', '`@here`')

        return content

    async def populate_db(self):
        messages_to_add = []
        for channel in self.get_all_channels():
            # Ignore all channels that are not Text Channels (Like Voice Channels)
            if not type(channel) == discord.TextChannel:
                continue
            try:
                async for message in channel.history(limit=5_000):
                    if self.is_valid_message(message):
                        content = self.clean_message(message.content, message.channel.id)
                        to_add = {
                            "message_id": message.id,
                            "content": content,
                            "author_name": message.author.name,
                            "author_id": message.author.id,
                            "channel_id": message.channel.id,
                            "timestamp": message.created_at
                        }
                        messages_to_add.append(to_add)
            except Exception:
                pass
        with db.atomic():
            for msg in messages_to_add:
                try:
                    Message.insert(**msg).on_conflict(
                        conflict_target=(Message.message_id,),
                        preserve=(
                            Message.message_id,
                            Message.author_id,
                            Message.author_name,
                            Message.channel_id,
                            Message.timestamp
                        ),
                        update={Message.content: msg.get('content')}).execute()
                except Exception as e:
                    db.rollback()
                    print(f'{e}: {msg}')
        print('Finished populating DB.')

    @staticmethod
    def db_setup():
        """
        Setup the bot's database, creates necessary tables if not yet created
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
