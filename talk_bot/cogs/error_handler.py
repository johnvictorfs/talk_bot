import traceback
import datetime
import logging

import discord
from discord.ext import commands


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def bot_check(ctx: commands.Context, **kwargs):
        """This runs at the start of every command"""
        await ctx.trigger_typing()
        time = datetime.datetime.utcnow()
        msg = f"'{ctx.command}' ran by '{ctx.author}' as '{ctx.invoked_with}' at {time}. with '{ctx.message.content}'"
        logging.info(msg)
        print(msg)
        return True

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        prefix = self.bot.settings.get('prefix')
        arguments_error = [
            commands.MissingRequiredArgument,
            commands.BadArgument,
            commands.TooManyArguments,
        ]
        command = None
        arguments = None
        if any([isinstance(error, arg_error) for arg_error in arguments_error]):
            if ctx.command.qualified_name == 'ignore':
                command = "ignore"
                arguments = f"`<channel>`"
            elif ctx.command.qualified_name == 'unignore':
                command = "unignore"
                arguments = f"`<channel>`"
            embed = discord.Embed(
                title=f"Usage of command '{command}'",
                description=f"`<argument>` : Obrigatory\n`(argument|default)` : Optional\n\n"
                f"{prefix}{command} {arguments}\n",
                color=discord.Colour.blue()
            )
            try:
                await ctx.send(embed=embed)
            except discord.errors.Forbidden:
                await ctx.send("Erro. Not enough permissions to send an embed.")
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is disabled.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can not be used in private messages.")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("This command can only be used by the bot's owner.")
        elif isinstance(error, commands.MissingPermissions):
            permissions = [f"***{perm.title().replace('_', ' ')}***" for perm in error.missing_perms]
            await ctx.send(f"You need the following permissions to do that: {', '.join(permissions)}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"You already used this comman recently. "
                f"Wait another {error.retry_after:.1f}s to use it again"
            )
        elif isinstance(error, commands.BotMissingPermissions):
            permissions = [f"***{perm.title().replace('_', ' ')}***" for perm in error.missing_perms]
            await ctx.send(f"I need the following permissions to do that: {', '.join(permissions)}")
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.send(f"You don't have permission to do that.")
        else:
            await ctx.send(f"Unknown error. The logs of this error have been sent to a Dev and will be fixed shortly.")
            tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            await self.bot.send_logs(error, tb, ctx)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
