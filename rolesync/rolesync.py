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
        self.config = Config.get_conf(self, 143056204359270400)
        asyncio.ensure_future(self.init_config())

    async def init_config(self):
        try:
            self.main_guild = await self.config.MAIN_GUILD()
        except:
            self.main_guild = 0
            await self.config.MAIN_GUILD.set(self.main_guild)

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
        await self.config.MAIN_GUILD.set(self.main_guild)