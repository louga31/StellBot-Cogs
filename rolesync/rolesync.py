import asyncio
import locale

import discord
from redbot.core import Config, commands
from redbot.core.bot import RedBase

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

class RoleSync(commands.Cog):
    """Synchronisation des rôles"""

    def __init__(self, bot):
        self.bot = bot
        asyncio.ensure_future(self.init_config())

    async def init_config(self):
        """Init cogs config"""
        self.config = Config.get_conf(self, 143056204359270400)

        default_global = {
            "Main_Guild": 0
        }
        default_guild = {
            "Wolf_Role": 0,
            "Member_Role": 0
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

        self.main_guild = self.bot.get_guild(await self.config.Main_Guild())

    async def get_colour(self, channel):
        """Get Bot's main colour"""
        return await RedBase.get_embed_colour(self.bot, channel)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Member join event"""
        if member.guild == self.main_guild:
            for guild in self.bot.guilds:
                if guild != self.main_guild:
                    if not guild.get_member(member.id) is None:
                        wolf_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Wolf_Role())
                        await member.add_roles(wolf_role, reason="L'utilisateur est wolf")
        else:
            if not self.main_guild.get_member(member.id) is None:
                if self.main_guild.get_role(await self.config.guild(self.main_guild).Wolf_Role()) in self.main_guild.get_member(member.id).roles:
                    if not member.guild.get_role(await self.config.guild(member.guild).Member_Role()) in member.roles:
                        member_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Member_Role())
                        await member.add_roles(member_role, reason="L'utilisateur est membre")

    @commands.group(name="rolesync")
    async def rolesync(self, ctx):
        """Commande principale de RoleSync"""

    @rolesync.group(name="set")
    async def _set(self, ctx):
        """Configuration de rolesync"""
    
    @_set.command()
    async def mainguild(self, ctx):
        """Definit le serveur principal"""
        await self.config.Main_Guild.set(int(ctx.guild.id))
        await self.init_config()
        await ctx.send(f"Serveur principal définit sur `{ctx.guild.name}`")

    @_set.command()
    async def wolfrole(self, ctx):
        """Definit le role wolf de ce serveur"""
        if len(ctx.message.role_mentions) == 0:
            await ctx.send("Veuillez mentionner un role")
            return
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Wolf_Role.set(role.id)
        await ctx.send(f"Role loup définit sur {role.mention}")

    @_set.command()
    async def memberrole(self, ctx):
        """Definit le role membre de ce serveur"""
        if len(ctx.message.role_mentions) == 0:
            await ctx.send("Veuillez mentionner un role")
            return
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Member_Role.set(role.id)
        await ctx.send(f"Role membre définit sur {role.mention}")

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def set_admin(self, ctx):
        members = ctx.message.mentions
        for member in members:
            admin_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Admin_Role())
            await member.add_roles(admin_role, reason="Commande forcée")
    
    @commands.guild_only()
    @commands.command(pass_context=True)
    async def remove_admin(self, ctx):
        members = ctx.message.mentions
        for member in members:
            admin_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Admin_Role())
            await member.remove_roles(admin_role, reason="Commande forcée")
