from redbot.core import commands, checks, Config
import discord.utils
import discord
import locale
import datetime
import asyncio, aiohttp
import math
from bs4 import BeautifulSoup
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

class SC(commands.Cog):
    """Commandes de Star Citizen"""
    @commands.command(pass_context=True)
    async def ship(self, ctx, vaisseau):
        """Affiche les informations du vaisseaux demandé"""
        quote_page = "https://starcitizen.tools/" + vaisseau
        em = discord.Embed(title="Star Citizen", description="Chargement des données du vaisseau", colour=0x0E82AF)
        message = await ctx.send(embed=em)
        async with aiohttp.ClientSession() as session:
            async with session.get(quote_page) as page:
                if page.status == 200:
                    soup = BeautifulSoup(await page.text(), 'html.parser')
                    table = soup.find('table', attrs={'class': 'infobox-table'})
                    brand = table.findNext('td', attrs={'class': 'brand'}).findNext('a').text
                    size = table.findNext('td', attrs={'class': 'category'}).findNext('a').text
                    maxcrew = table.findAll('tr')[7].findAll('td')[1].text
                    cargo = table.findAll('tr')[8].findAll('td')[1].text
                    price = table.findNext('tr', attrs={'id': 'pledgecost'}).findAll('td')[1].findNext('span').text + '$'
                    em = discord.Embed(title="", description='[{}]({})'.format(vaisseau, quote_page), colour=0x0E82AF)
                    em.add_field(name="Constructeur:", value=brand, inline=True)
                    em.add_field(name="Taille:", value=size, inline=True)
                    em.add_field(name="Crew Maximum:", value=maxcrew, inline=True)
                    em.add_field(name="Capacité cargo:", value=cargo, inline=True)
                    em.add_field(name="Prix:", value=price, inline=True)
                    em.set_image(url="https://starcitizen.tools/images/thumb/0/0d/Carrack_Front_Top_Space.png/512px-Carrack_Front_Top_Space.png")
                    await message.edit(embed=em)