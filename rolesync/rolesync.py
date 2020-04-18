import concurrent.futures
import functools
import asyncio
import locale
from redbot.core import Config, commands
from redbot.core.data_manager import cog_data_path
import discord

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

class RoleSync(commands.Cog):
    """Synchronisation des rôles"""

    def __init__(self, bot):
        self.bot = bot
        asyncio.ensure_future(self.init_config())

    async def init_config(self):
        self.config = Config.get_conf(self, 143056204359270400)

        default_global = {
            "Main_Guild": 0
        }
        default_guild = {
            "Wolf_Role": 0,
            "Solo_Role": 0
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

        self.main_guild = await self.config.Main_Guild()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Member join event"""
        pass

    @commands.group(name="rolesync")
    async def rolesync(self, ctx):
        """Commande principale de RoleSync"""
        await ctx.message.delete()
        pass

    @rolesync.group(name="set")
    async def _set(self, ctx):
        """Configuration de rolesync"""
        pass
    
    @_set.command()
    async def mainguild(self, ctx):
        self.main_guild = int(ctx.guild.id)
        await self.config.Main_Guild.set(self.main_guild)
        ctx.send(f"Serveur principal définit sur `{ctx.guild.name}`")

    @_set.command()
    async def wolfrole(self, ctx):
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Wolf_Role.set(role.id)
        ctx.send(f"Role loup définit sur `{role.mention}`")

    @_set.command()
    async def solorole(self, ctx):
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Solo_Role.set(role.id)
        ctx.send(f"Role solitaire définit sur `{role.mention}`")