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
            "Solo_Role": 0
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
                    solo_role = discord.utils.get(guild.roles, id=await self.config.guild(guild).Solo_Role())
                    await member.remove_roles(solo_role, reason="L'utilisateur a rejoint le serveur principal")
        else:
            if self.main_guild.get_role(await self.config.guild(self.main_guild).Admin_Role()) in self.main_guild.get_member(member.id).roles:
                admin_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Admin_Role())
                await member.add_roles(admin_role, reason="L'utilisateur est admin")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Member leave event"""
        if member.guild == self.main_guild:
            wolf_role = discord.utils.get(member.guild.roles, id=await self.config.guild(member.guild).Wolf_Role())
            if wolf_role in member.roles:
                for guild in self.bot.guilds:
                    if guild != self.main_guild:
                        solo_role = discord.utils.get(guild.roles, id=await self.config.guild(guild).Solo_Role())
                        await member.add_roles(solo_role, reason="L'utilisateur a quitté le serveur principal")

    @commands.group(name="rolesync")
    async def rolesync(self, ctx):
        """Commande principale de RoleSync"""
    
    @rolesync.command()
    async def forcerolecheck(self, ctx):
        """Force la recherche et attribution du role solitaire"""
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Attribution des rôles en cours", description="Merci de patienter")
        work_message = await ctx.send(embed=embed)
        count = 0
        for guild in self.bot.guilds:
            if guild != self.main_guild:
                wolf_role = discord.utils.get(guild.roles, id=await self.config.guild(guild).Wolf_Role())
                for member in guild.members:
                    if wolf_role in member.roles:
                        if not member in self.main_guild.members:
                            solo_role = discord.utils.get(guild.roles, id=await self.config.guild(guild).Solo_Role())
                            await member.add_roles(solo_role, reason="L'utilisateur n'est pas sur le serveur principal")
                            count += 1
        embed = discord.Embed(colour=0x00ff40, title="Attibution terminée", description=f"{count} roles attribués")
        work_message.edit(embed=embed)

    @rolesync.group(name="set")
    async def _set(self, ctx):
        """Configuration de rolesync"""
    
    @_set.command()
    async def mainguild(self, ctx):
        """Definit le serveur principal"""
        self.main_guild = self.bot.get_guild(int(ctx.guild.id))
        await self.config.Main_Guild.set(self.main_guild.id)
        await ctx.send(f"Serveur principal définit sur `{ctx.guild.name}`")

    @_set.command()
    async def adminrole(self, ctx):
        """Definit le role admin de ce serveur"""
        if len(ctx.message.role_mentions) == 0:
            await ctx.send("Veuillez mentionner un role")
            return
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Admin_Role.set(role.id)
        await ctx.send(f"Role admin définit sur {role.mention}")

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
    async def solorole(self, ctx):
        """Definit le role solitaire de ce serveur"""
        if len(ctx.message.role_mentions) == 0:
            await ctx.send("Veuillez mentionner un role")
            return
        role = ctx.message.role_mentions[0]
        await self.config.guild(ctx.guild).Solo_Role.set(role.id)
        await ctx.send(f"Role solitaire définit sur {role.mention}")
