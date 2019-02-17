import re

from discord.ext import commands

from talk_bot.orm.models import IgnoredChannel


class ManagementCommands:

    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_channels=True)
    @commands.command(aliases=['ignore'])
    async def ignore_channel(self, ctx: commands.Context, channel_str: str):
        """
        Ignores a channel so new messages from it are not stored in the bot's database

        Requires:
            Permissions:
                - Manage Server
        """

        # Searches for channel id in string like'<#546528012430999552>'
        channel_id = re.search(r'\d+', channel_str)

        if not channel_id:
            return await ctx.send(f'Invalid Channel: {channel_str}')

        channel_id = int(channel_id.group())
        IgnoredChannel.create(channel_id=channel_id)
        return await ctx.send(f'Channel <#{channel_id}> ignored successfully.')

    @commands.has_permissions(manage_channels=True)
    @commands.command(aliases=['unignore'])
    async def unignore_channel(self, ctx: commands.Context, channel_str: str):
        """
        Un-ignores a channel so new messages from it are again stored in the bot's database

        Requires:
            Permissions:
                - Manage Server
        """

        # Searches for channel id in string like'<#546528012430999552>'
        channel_id = re.search(r'\d+', channel_str)

        if not channel_id:
            return await ctx.send(f'Invalid Channel: {channel_str}')

        channel_id = int(channel_id.group())
        channel = IgnoredChannel.get(IgnoredChannel.channel_id == channel_id)
        if not channel:
            return await ctx.send(f'Channel <#{channel_id}> is already not being ignored.')

        IgnoredChannel.delete().where(IgnoredChannel.channel_id == channel_id).execute()
        return await ctx.send(f'Channel <#{channel_id}> is no longer being ignored.')


def setup(bot):
    bot.add_cog(ManagementCommands(bot))
