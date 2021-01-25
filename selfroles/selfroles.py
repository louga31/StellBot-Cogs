from typing import cast
import discord
from redbot.core import commands, checks, Config
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.bot import RedBase
import random
import string
import aiohttp
import asyncio
import base64
import datetime
import math
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from redbot.core.utils.menus import (
    menu,
    DEFAULT_CONTROLS,
    prev_page,
    next_page,
    close_menu,
    start_adding_reactions,
)
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support

if listener is None:  # thanks Sinbad
    def listener(name=None):
        return lambda x: x


class SelfRoles(commands.Cog):
    """SelfRoles commands"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 45463543548)
        self.users = {}

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
        react_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not react_message.embeds:
            return
        embed = react_message.embeds[0]
        try:
            if not embed.footer.text.startswith('React ID:'):
                return
        except:
            return
        unformatted_options = [x.strip() for x in embed.description.split('\n')]
        opt_dict = {x[:2]: x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
            else {x[:1]: x[2:] for x in unformatted_options}
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if str(payload.emoji) in opt_dict.keys():
            role = guild.get_role(int(opt_dict[str(payload.emoji)].split('&')[1].split('>')[0]))
            await self.give_role(role, member)

    @listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        react_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not react_message.embeds:
            return
        embed = react_message.embeds[0]
        try:
            if not embed.footer.text.startswith('React ID:'):
                return
        except:
            return
        unformatted_options = [x.strip() for x in embed.description.split('\n')]
        opt_dict = {x[:2]: x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
            else {x[:1]: x[2:] for x in unformatted_options}
        guild = self.bot.get_guild(payload.guild_id)     
        member = guild.get_member(payload.user_id)
        if str(payload.emoji) in opt_dict.keys():
            role = guild.get_role(int(opt_dict[str(payload.emoji)].split('&')[1].split('>')[0]))
            await self.remove_role(role, member)

    @commands.guild_only()       
    @commands.command(pass_context=True)
    async def selfroles(self, ctx, *options: str):
        await ctx.message.delete()
        if len(options) < 1:
            await ctx.send('You need at least 1 role!')
            return
        if len(options) > 10:
            await ctx.send('You cannot make a selfrole message for more than 10 roles!')
            return

        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
        description = ""
        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.guild), title="Réagissez à ce message pour obtenir vos roles", description=''.join(description))
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text='React ID: {}'.format(react_message.id))
        await react_message.edit(embed=embed)