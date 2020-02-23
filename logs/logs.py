from redbot.core import commands, checks, Config
from discord.utils import get
import discord
import locale
from datetime import datetime
client = discord.Client()

class LOGS(commands.Cog):
    """LOGS"""

    def __init__(self, bot):
        self.bot = bot

    @client.event
    async def on_message_delete(self, message):
        if message.author is message.author.bot:
            pass
        time = datetime.datetime.now()
        cleanmsg = message.content
        for i in message.mentions:
            cleanmsg = cleanmsg.replace(i.mention, str(i))
        fmt = '%H:%M:%S'
        name = message.author
        name = " ~ ".join((name.name, name.nick)) if name.nick else name.name
        delmessage = discord.Embed(description=name, colour=discord.Color.purple())
        infomessage = "A message by __{}__, was deleted in {}".format(
            message.author.nick if message.author.nick else message.author.name, message.channel.mention)
        delmessage.add_field(name="Info:", value=infomessage, inline=False)
        delmessage.add_field(name="Message:", value=cleanmsg)
        delmessage.set_footer(text="User ID: {}".format(message.author.id))
        delmessage.set_author(name=time.strftime(fmt) + " - Deleted Message", url="http://i.imgur.com/fJpAFgN.png")
        delmessage.set_thumbnail(url="http://i.imgur.com/fJpAFgN.png")
        user = get(self.bot.get_user(175217614706966528))
        print(user)
        await user.dm_channel.send(embed=delmessage)
