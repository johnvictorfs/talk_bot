import re

from discord.ext import commands

from talk_bot.orm.models import IgnoredChannel


class ManagementCommands(commands.Cog):

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
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return await ctx.send(f'Invalid Channel: {channel_str}')

        # Only allow a channel to be ignored if the ignore command was sent in the same guild as that channel
        if channel in ctx.guild.channels:
            ignored, created = IgnoredChannel.get_or_create(channel_id=channel_id)
            if not created:
                return await ctx.send(f'Channel <#{channel_id}> is already ignored.')
            return await ctx.send(f'Channel <#{channel_id}> ignored successfully.')
        else:
            return await ctx.send("You can only ignore channels from the same server you're sending this command.")

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

    @commands.is_owner()
    @commands.command()
    async def clean_db(self, ctx: commands.Context):
        await ctx.send("Cleaning the bot's database...")
        await self.bot.clean_db()
        return await ctx.send("Sucessfully cleaned the bot's database.")


def setup(bot):
    bot.add_cog(ManagementCommands(bot))
