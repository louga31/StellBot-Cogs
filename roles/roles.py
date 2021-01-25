from typing import cast
import discord
import asyncio
from redbot.core import commands, Config
from redbot.core.bot import RedBase
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support

if listener is None:  # thanks Sinbad
    def listener(name=None):
        return lambda x: x


class Roles(commands.Cog):
    """Roles commands"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 72451682326428)
        asyncio.ensure_future(self.set_roles())

    async def set_roles(self):
        self.roles = await self.config.ROLES()
    
    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)
    
    async def give_role(self, role: discord.Role, member: discord.Member):
        await member.add_roles(role, reason="Self give")
        return

    async def remove_role(self, role, member):
        await member.remove_roles(role, reason="Self remove")
        return

    @listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # react_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        # if not react_message.embeds:
        #     return
        # embed = react_message.embeds[0]
        # try:
        #     if not embed.footer.text.startswith('React ID:'):
        #         return
        # except:
        #     return
        # unformatted_options = [x.strip() for x in embed.description.split('\n')]
        # opt_dict = {x[:2]: x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
        #     else {x[:1]: x[2:] for x in unformatted_options}
        # guild = self.bot.get_guild(payload.guild_id)
        # member = guild.get_member(payload.user_id)
        # if str(payload.emoji) in opt_dict.keys():
        #     role = guild.get_role(int(opt_dict[str(payload.emoji)].split('&')[1].split('>')[0]))
        #     await self.give_role(role, member)
        pass

    @listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # react_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        # if not react_message.embeds:
        #     return
        # embed = react_message.embeds[0]
        # try:
        #     if not embed.footer.text.startswith('React ID:'):
        #         return
        # except:
        #     return
        # unformatted_options = [x.strip() for x in embed.description.split('\n')]
        # opt_dict = {x[:2]: x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
        #     else {x[:1]: x[2:] for x in unformatted_options}
        # guild = self.bot.get_guild(payload.guild_id)     
        # member = guild.get_member(payload.user_id)
        # if str(payload.emoji) in opt_dict.keys():
        #     role = guild.get_role(int(opt_dict[str(payload.emoji)].split('&')[1].split('>')[0]))
        #     await self.remove_role(role, member)
        pass

    @commands.guild_only()       
    @commands.command(pass_context=True)
    async def rolemessage(self, ctx, messageid: int, *roles: str):
        await ctx.message.delete()
        if len(roles) < 1:
            await ctx.send('You need at least 1 role!')
            return
        if len(roles) > 10:
            await ctx.send('You cannot make a selfrole message for more than 10 roles!')
            return