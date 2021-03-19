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

def from_roles(guild: discord.Guild, x: Any) -> discord.Role:
    return [guild.get_role(y) for y in x]

async def from_emojis(guild: discord.Guild, x: Any) -> discord.Emoji:
    return [await guild.fetch_emoji(y) for y in x]

def to_id(x: Any) -> int:
    assert isinstance(x, discord.Role) or isinstance(x, discord.Emoji) or isinstance(x, discord.PartialEmoji)
    return x.id

@dataclass
class RoleMessage:
    roles: List[discord.Role]
    emojis: List[discord.Emoji]
    status: int

    @staticmethod
    async def from_dict(guild: discord.Guild, obj: Any) -> 'RoleMessage':
        assert isinstance(obj, dict)
        roles = from_roles(guild, obj.get("roles"))
        emojis = await from_emojis(guild, obj.get("emojis"))
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
        await asyncio.sleep(1)
        self.role_messages = await self.config.role_messages()
        if self.role_messages is None:
            self.role_messages = {}
            await self.config.role_messages.set(self.role_messages)
        for messageid, config in self.role_messages.items():
            self.role_messages[messageid] = await RoleMessage.from_dict(self.bot.get_guild(705722982814711808), config)

    async def save_config(self):
        await self.config.role_messages.set({messageid:config.to_dict() for messageid, config in self.role_messages.items()})
    
    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)
    
    async def give_role(self, role: discord.Role, member: discord.Member):
        await member.add_roles(role, reason='Self give')
        return

    async def remove_role(self, role: discord.Role, member: discord.Member):
        await member.remove_roles(role, reason='Self remove')
        return
    
    async def process_config_step(self, channel: discord.TextChannel, emoji: discord.PartialEmoji, self_message: discord.PartialMessage, step_message: discord.Message):
        await self_message.add_reaction(emoji)
        await step_message.clear_reactions()
        self_id = str(self_message.id)

        self.role_messages[self_id].status += 1
        self.role_messages[self_id].emojis.append(emoji)
        await self.save_config()
        
        if self.role_messages[self_id].status < len(self.role_messages[self_id].roles):
            embed = discord.Embed(colour=await self.get_colour(channel), description=f"Merci d'ajouter à ce message la réaction que vous voulez pour le rôle {self.role_messages[self_id].roles[self.role_messages[self_id].status].mention}")
            embed.set_footer(text=f'Self ID: {self_id}')
            await step_message.edit(embed=embed)
        else:
            await step_message.delete()

    @listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = cast(discord.Guild, self.bot.get_guild(payload.guild_id))
        channel = cast(discord.TextChannel, guild.get_channel(payload.channel_id))
        react_message = cast(discord.Message, await channel.fetch_message(payload.message_id))
        
        if not react_message.embeds:
            react_id = str(react_message.id)
            if not react_id in self.role_messages:
                return
            if not payload.emoji in self.role_messages[react_id].emojis:
                return
            await self.give_role(self.role_messages[react_id].roles[self.role_messages[react_id].emojis.index(payload.emoji)], guild.get_member(payload.user_id))
            return
        embed = react_message.embeds[0]
        try:
            if not embed.footer.text.startswith('Self ID:'):
                return
        except:
            return
        
        self_message = cast(discord.Message, channel.get_partial_message(embed.footer.text.split(': ')[1]))
        await self.process_config_step(guild.get_channel(payload.channel_id), payload.emoji, self_message, react_message)
        
    @listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = cast(discord.Guild, self.bot.get_guild(payload.guild_id))
        channel = cast(discord.TextChannel, guild.get_channel(payload.channel_id))
        react_message = cast(discord.Message, await channel.fetch_message(payload.message_id))
        react_id = str(react_message.id)
        if not react_id in self.role_messages:
            return
        if not payload.emoji in self.role_messages[react_id].emojis:
            return
        await self.remove_role(self.role_messages[react_id].roles[self.role_messages[react_id].emojis.index(payload.emoji)], guild.get_member(payload.user_id))
    
    @commands.guild_only()
    @commands.command(pass_context=True)
    async def cleanself(self, ctx):
        self.role_messages = {}
        await self.config.role_messages.set(self.role_messages)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="SelfRoles cleaned")
        await ctx.send(embed=embed)
    
    @commands.guild_only()       
    @commands.command(pass_context=True)
    async def rolemessage(self, ctx, message: discord.Message, *roles: discord.Role):
        await ctx.message.delete()
        if len(roles) < 1:
            embed=discord.Embed(title='You need at least 1 role!', color=0xff0000)
            await ctx.send(embed=embed)
            return
        if len(roles) > 10:
            embed=discord.Embed(title='You cannot make a selfrole message for more than 10 roles!', color=0xff0000)
            await ctx.send(embed=embed)
            return
        message_id = str(message.id)
        self.role_messages[message_id] = RoleMessage(list(roles), [], 0)
        await self.save_config()
        embed = discord.Embed(colour=await self.get_colour(message.channel), description=f"Merci d'ajouter à ce message la réaction que vous voulez pour le rôle {self.role_messages[message_id].roles[self.role_messages[message_id].status].mention}")
        embed.set_footer(text=f'Self ID: {message_id}')
        await message.channel.send(embed=embed)
        