from dataclasses import dataclass
from typing import List, Any, TypeVar, Callable, Type, cast
import discord
import asyncio
import locale
from discord import embeds
from discord import reaction
from redbot.core import commands, Config
from redbot.core.bot import RedBase

T = TypeVar("T")
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
listener = getattr(commands.Cog, 'listener', None)  # red 3.0 backwards compatibility support

if listener is None:  # thanks Sinbad
    def listener(name=None):
        return lambda x: x

def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]

def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x

def from_role(guild: discord.Guild, x: Any) -> discord.Role:
    assert isinstance(x, int) and not isinstance(x, bool)
    return guild.get_role(x)

def from_emoji(guild: discord.Guild, x: Any) -> discord.Emoji:
    assert isinstance(x, int) and not isinstance(x, bool)
    return guild.fetch_emoji(x)

def to_id(x: Any) -> int:
    assert isinstance(x, discord.Role) or isinstance(x, discord.Emoji)
    return x.id

@dataclass
class RoleMessage:
    roles: List[discord.Role]
    emojis: List[discord.Emoji]
    status: int

    @staticmethod
    def from_dict(obj: Any) -> 'RoleMessage':
        assert isinstance(obj, dict)
        roles = from_list(from_role, obj.get("roles"))
        emojis = from_list(from_emoji, obj.get("emojis"))
        status = from_int(obj.get("status"))
        return RoleMessage(roles, emojis, status)

    def to_dict(self) -> dict:
        result: dict = {}
        result["roles"] = from_list(to_id, self.roles)
        result["emojis"] = from_list(to_id, self.emojis)
        result["status"] = from_int(self.status)
        return result

class Roles(commands.Cog):
    """Roles commands"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 72451682326428)
        asyncio.ensure_future(self.set_roles())

    async def set_roles(self):
        self.role_messages = await self.config.role_messages()
        if self.role_messages is None:
            self.role_messages = {}
            await self.config.role_messages.set(self.role_messages)

    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)
    
    async def give_role(self, role: discord.Role, member: discord.Member):
        await member.add_roles(role, reason='Self give')
        return

    async def remove_role(self, role, member):
        await member.remove_roles(role, reason='Self remove')
        return
    
    async def process_step(self):
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
    async def rolemessage(self, ctx, message: discord.Message, *roles: discord.Role):
        print(roles)
        await ctx.message.delete()
        if len(roles) < 1:
            embed=discord.Embed(title='You need at least 1 role!', color=0xff0000)
            await ctx.send(embed=embed)
            return
        if len(roles) > 10:
            embed=discord.Embed(title='You cannot make a selfrole message for more than 10 roles!', color=0xff0000)
            await ctx.send(embed=embed)
            return
        self.role_messages[message.id] = RoleMessage(list(roles), [], 1).to_dict()
        await self.config.role_messages.set(self.role_messages)
        print(self.role_messages)
        embed = discord.Embed(colour=await self.get_colour(message.channel), title=f"Merci d'ajouter à ce message la réaction que vous voulez pour le rôle {self.role_messages[message.id].roles[self.role_messages[message.id].status]}")
        await message.channel.send(embed=embed)