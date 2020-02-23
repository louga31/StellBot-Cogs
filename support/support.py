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
import subprocess
import os

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support

if listener is None:  # thanks Sinbad
    def listener(name=None):
        return lambda x: x

class Support(commands.Cog):
    """Support system"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 15465415464689)
        asyncio.ensure_future(self.set_config())

    async def set_config(self):
        self.transcript_id = await self.config.TRANSCRIPT_ID()
        self.admin_role = await self.config.ADMIN_ROLE()

    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)

    async def create_ticket(self, index, member, category, guild):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_role(self.admin_role): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(f'📩-Ticket - {index}', overwrites=overwrites, category=category, reason="L'utilisateur a demandé de l'aide")
        await ticket_channel.send(f"{member.mention}\nDécrit ton problème ici, un administrateur te répondra vite")
        options = ["Close"]
        reactions = ['🔒']
        embed = discord.Embed(colour=0x00aa40, title="Support", description="Pour fermer le ticket, cliquez sur 🔒")
        react_message = await ticket_channel.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text='Ticket ID: {}'.format(index))
        tickets = await self.config.TICKETS()
        tickets[str(index)]=[ticket_channel.id, react_message.id]
        await self.config.TICKETS.set(tickets)
        users = await self.config.USERS()
        users[str(index)] = member.id
        await self.config.USERS.set(users)
        await react_message.edit(embed=embed)

    @listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author.id == payload.user_id:
            return
        if not message.embeds:
            return
        embed = message.embeds[0]
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        index = await self.config.INDEX()
        try:
            if embed.footer.text.startswith('Pannel ID:'):
                pass
        except:
            return
        if embed.footer.text.startswith('Pannel ID:'):
            await message.remove_reaction(payload.emoji, member)
            category_id = channel.category_id
            categories = guild.categories
            for k in categories:
                if k.id == category_id:
                    category = k
            await self.config.INDEX.set(index + 1)
            await self.create_ticket(index, member, category, guild)

        elif embed.footer.text.startswith('Ticket ID:'):
            await message.remove_reaction(payload.emoji, member)
            if str(payload.emoji) == '🔒':
                options = ['Oui', 'Non']
                reactions = ['✅', '❌']
                for reaction in reactions[:len(options)]:
                    await message.add_reaction(reaction)

            elif str(payload.emoji) == '✅':
                await message.clear_reactions()
                emb = message.embeds[0]
                embed = discord.Embed(colour=0xfbfe32, title="", description=f"Ticket fermé par {member.mention}")
                await channel.send(embed=embed)

                options = ['Réouvrir le Ticket', 'Supprimer le Ticket']
                reactions = ['🔓', '⛔']
                description = []
                for x, option in enumerate(options):
                    description += '\n {} {}'.format(reactions[x], option)
                index = emb.footer.text.split(':')[1][1:]

                users = await self.config.USERS()
                member = guild.get_member(users[str(index)])
                await channel.set_permissions(member, read_messages=False, send_messages=False, reason='Ticket fermé')
                await channel.edit(reason='Ticket fermé', name=f'🔒-Fermé - {index}')

                embed = discord.Embed(colour=0xd32f2f, title="Outils d'adminitration", description=''.join(description))
                react_message = await channel.send(embed=embed)
                for reaction in reactions[:len(options)]:
                    await react_message.add_reaction(reaction)
                embed.set_footer(text='Mod ID: {}'.format(index))
                await react_message.edit(embed=embed)

            elif str(payload.emoji) == '❌':
                await message.clear_reactions()
                options = ["Close"]
                reactions = ['🔒']
                for reaction in reactions[:len(options)]:
                    await message.add_reaction(reaction)

        elif embed.footer.text.startswith('Mod ID:'):
            if str(payload.emoji) == '🔓':
                await message.delete()
                embed = discord.Embed(colour=0x00aa40, title="", description=f"Ticket ouvert par {member.mention}")
                await channel.send(embed=embed)
                emb = message.embeds[0]
                index = emb.footer.text.split(':')[1][1:]
                users = await self.config.USERS()
                member = guild.get_member(users[str(index)])
                await channel.set_permissions(member, read_messages=True, send_messages=True)
                await channel.edit(reason='Ticket ouvert', name=f'📩-Ticket - {index}')
                tickets = await self.config.TICKETS()
                channel_id = tickets[str(index)][0]
                message_id = tickets[str(index)][1]
                channel = self.bot.get_channel(channel_id)
                react_message = await channel.fetch_message(message_id)
                options = ["Close"]
                reactions = ['🔒']
                for reaction in reactions[:len(options)]:
                    await react_message.add_reaction(reaction)
            elif str(payload.emoji) == '⛔':
                await message.delete()
                transcript = self.bot.get_channel(self.transcript_id)
                embed = discord.Embed(colour=0xfbfe32, title="", description=f"Transcript en cours de génération, le channel sera automatiquement supprimé")
                await channel.send(embed=embed)
                emb = message.embeds[0]
                index = emb.footer.text.split(':')[1][1:]
                users = await self.config.USERS()
                member = guild.get_member(users[str(index)])
                subprocess.call(['dotnet', '/data/DiscordChatExplorer/DiscordChatExporter.Cli.dll', 'export', '-c', f'{payload.channel_id}', '-t', 'NjA3OTcxODI4MDY5MTcxMjIy.XaESJQ.ergsHwUHUfCJFHXwb7bxKAE95Zk', '-b', '-o', f'/data/DiscordChatExplorer/transcript-{index}.html'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                presents = []
                async for message in channel.history(limit=5000):
                    if guild.get_member(message.author.id).mention not in presents:
                        presents.append(guild.get_member(message.author.id).mention)
                presents.pop(0)
                embed = discord.Embed(colour=0xfffc80, title=f"Ticket - {index}", description=f"Détails du transcript")
                embed.add_field(name='Propriétaire du ticket', value=f'{member.mention}', inline=False)
                if len(presents) != 0:
                    embed.add_field(name='Utilisateurs dans le transcript', value=' '.join(presents), inline=False)
                else:
                    embed.add_field(name='Utilisateurs dans le transcript', value='-', inline=False)
                await transcript.send(embed=embed, file=discord.File(f'/data/DiscordChatExplorer/transcript-{index}.html'))
                os.remove(f'/data/DiscordChatExplorer/transcript-{index}.html')
                await channel.delete(reason='Ticket Supprimé')
                tickets = await self.config.TICKETS()
                del tickets[str(index)]
                await self.config.TICKETS.set(tickets)
                users = await self.config.USERS()
                del users[str(index)]
                await self.config.USERS.set(users)

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def pannel(self, ctx):
        await ctx.message.delete()
        options = ["Ticket"]
        reactions = ['📩']
        embed = discord.Embed(colour=0x00aa40, title="Support", description="Pour ouvrir un ticket, cliquez sur 📩")
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
                await react_message.add_reaction(reaction)
        embed.set_footer(text='Pannel ID: {}'.format(react_message.id))
        await react_message.edit(embed=embed)
    
    @commands.command(pass_context=True)
    async def support_clean(self, ctx):
        await self.config.INDEX.set(0)
        await self.config.USERS.set({})
        await self.config.TICKETS.set({})
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Support datas cleaned")
        await ctx.send(embed=embed)
    
    @commands.group(pass_context=True)
    async def support_set(self, ctx):
        """Set support settings."""
        pass

    @support_set.command()
    async def transcript_channel(self, ctx, channel_id: int):
        self.transcript_id = channel_id
        await self.config.TRANSCRIPT_ID.set(self.transcript_id)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Channel transcript définit")
        await ctx.send(embed=embed)

    @support_set.command()
    async def admin_role(self, ctx, admin_role_id: int):
        self.admin_role = admin_role_id 
        await self.config.ADMIN_ROLE.set(self.admin_role)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Role admin définit")
        await ctx.send(embed=embed)