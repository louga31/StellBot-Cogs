import asyncio
import locale
from typing import cast
from redbot.core import commands, Config
from redbot.core.bot import RedBase
import discord
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support


class Poll(commands.Cog):
    """Polls"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 45463543548)
        self.polls = []
        asyncio.ensure_future(self.set_polls())

    async def set_polls(self):
        self.polls = await self.config.POLLS()

    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)

    async def edit_poll(self, message, poll):
        polls = []
        description = []
        embed = message.embeds[0]
        unformatted_options = [x.strip() for x in embed.description.split('\n')]
        options_dict = poll['options']
        options = []
        for x in options_dict:
            options.append(x)
        for k in options:
            polls.append(0)
        if poll["multi"]:
            for x, y in poll['pollers'].items():
                for z in y:
                    if z != 'null':
                        polls[options.index(z)] += 1
        else:
            for x, y in poll['pollers'].items():
                if y != 'null':
                    polls[options.index(y)] += 1
        for j, poll in enumerate(polls):
            option = unformatted_options[j]
            option = option[:-6]
            option = option.split(' --- ')
            description += '\n {}'.format(option[0])
            description += ' --- ' + str(poll) + ' polls'
        # ['{}: {}'.format(opt_dict[key], tally[key]) ]
        embed2 = discord.Embed(colour=embed.colour, title=embed.title, description=''.join(description))
        embed2.set_footer(text=embed.footer.text)
        await message.edit(embed=embed2)

    @listener()
    async def on_raw_reaction_add(self, payload):
        poll_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if poll_message.author.id == payload.user_id:
            return
        if not poll_message.embeds:
            return
        embed = poll_message.embeds[0]
        try:
            if not embed.footer.text.startswith('Poll ID:'):
                return
        except:
            return
        for k in range(len(self.polls)):
            if self.polls[k]['id'] == str(poll_message.id):
                poll = self.polls[k]
                index = k
        pollers = poll['pollers']
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        for x, y in poll['options'].items():
            if y == str(payload.emoji):
                option = x
                break
        if poll["multi"]:
            if str(payload.user_id) in pollers and option in pollers[str(payload.user_id)]:
                poll['pollers'][str(payload.user_id)].pop(poll['pollers'][str(payload.user_id)].index(option))
            elif str(payload.user_id) in pollers:
                poll['pollers'][str(payload.user_id)].append(option)
            else:
                poll['pollers'][str(payload.user_id)] = [option]
        else:
            if str(payload.user_id) in pollers:
                poll['pollers'].pop(str(payload.user_id))
            poll['pollers'][str(payload.user_id)] = option

        self.polls[index] = poll
        await self.edit_poll(poll_message, poll)
        await poll_message.remove_reaction(payload.emoji, member)
        await self.config.POLLS.set(self.polls)

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def poll(self, ctx, question, *options: str):
        await ctx.message.delete()
        if len(options) <= 1:
            await ctx.send('You need more than one option to make a poll!')
            return
        if len(options) > 10:
            await ctx.send('You cannot make a poll for more than 10 things!')
            return

        if len(options) == 2 and ((options[0] == 'Oui' and options[1] == 'Non') or (options[0] == 'oui' and options[1] == 'Non') or (options[0] == 'oui' and options[1] == 'non') or (options[0] == 'Oui' and options[1] == 'non')):
            reactions = ['✅', '❌']
            emoji = {"oui": "✅", "non": "❌"}
        elif len(options) == 3 and ((options[0] == 'Oui' and options[1] == 'Non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'Non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'non' and options[2] == 'joker') or (options[0] == 'Oui' and options[1] == 'non' and options[2] == 'joker') or (options[0] == 'Oui' and options[1] == 'Non' and options[2] == 'joker')):
            reactions = ['✅', '❌', '🃏']
            emoji = {"oui": "✅", "non": "❌", "joker": "🃏"}

        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
            emoji = {"un": "1⃣", "deux": "2⃣", "trois": "3⃣", "quatre": "4⃣", "cinq": "5⃣", "six": "6⃣", "sept": "7⃣", "huit": "8⃣", "neuf": "9⃣", "dix": "🔟"}
        emojis = {}
        description = []
        polls = []
        for x, option in enumerate(options):
            emojis[list(emoji.keys())[x]] = emoji[list(emoji.keys())[x]]
            polls.append(0)
            description += '\n {} {}'.format(reactions[x], option)
            description += ' --- ' + str(polls[x]) + ' polls'
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title=question, description=''.join(description))
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text='Poll ID: {}'.format(react_message.id))
        await react_message.edit(embed=embed)
        pollers = {f"{react_message.author.id}": "null"}
        self.polls.append({"id": f"{react_message.id}", "options": emojis, "pollers": pollers, "multi": False})
        await self.config.POLLS.set(self.polls)
    
    @commands.guild_only()
    @commands.command(pass_context=True)
    async def multi_poll(self, ctx, question, *options: str):
        await ctx.message.delete()
        if len(options) <= 1:
            await ctx.send('You need more than one option to make a poll!')
            return
        if len(options) > 10:
            await ctx.send('You cannot make a poll for more than 10 things!')
            return

        if len(options) == 2 and ((options[0] == 'Oui' and options[1] == 'Non') or (options[0] == 'oui' and options[1] == 'Non') or (options[0] == 'oui' and options[1] == 'non') or (options[0] == 'Oui' and options[1] == 'non')):
            reactions = ['✅', '❌']
            emoji = {"oui": "✅", "non": "❌"}
        elif len(options) == 3 and ((options[0] == 'Oui' and options[1] == 'Non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'Non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'non' and options[2] == 'Joker') or (options[0] == 'oui' and options[1] == 'non' and options[2] == 'joker') or (options[0] == 'Oui' and options[1] == 'non' and options[2] == 'joker') or (options[0] == 'Oui' and options[1] == 'Non' and options[2] == 'joker')):
            reactions = ['✅', '❌', '🃏']
            emoji = {"oui": "✅", "non": "❌", "joker": "🃏"}

        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
            emoji = {"un": "1⃣", "deux": "2⃣", "trois": "3⃣", "quatre": "4⃣", "cinq": "5⃣", "six": "6⃣", "sept": "7⃣", "huit": "8⃣", "neuf": "9⃣", "dix": "🔟"}
        emojis = {}
        description = []
        polls = []
        for x, option in enumerate(options):
            emojis[list(emoji.keys())[x]] = emoji[list(emoji.keys())[x]]
            polls.append(0)
            description += '\n {} {}'.format(reactions[x], option)
            description += ' --- ' + str(polls[x]) + ' polls'
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title=question, description=''.join(description))
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text='Poll ID: {}'.format(react_message.id))
        await react_message.edit(embed=embed)
        pollers = {f"{react_message.author.id}": ["null"]}
        self.polls.append({"id": f"{react_message.id}", "options": emojis, "pollers": pollers, "multi": True})
        await self.config.POLLS.set(self.polls)

    @commands.command(pass_context=True)
    async def poll_result(self, ctx, id: str):
        for poll in self.polls:
            if poll["id"] == id:
                pollers = poll['pollers']
                del pollers[str(self.bot.user.id)]
                embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Résultats du vote (Message 1)")
                for index, (x, y) in enumerate(pollers.items()):
                    if index%20 == 0 and index != 0:
                        await ctx.send(embed=embed)
                        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Résultats du vote (Message {})".format((index//20)+1))
                    embed.add_field(name="Vote", value=f"<@{x}> --- {y}", inline=False)
                await ctx.send(embed=embed)
                return

    @commands.command(pass_context=True)
    async def poll_clean(self, ctx):
        self.polls = []
        await self.config.POLLS.set(self.polls)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Polls cleaned")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def say(self, ctx, *message):
        await ctx.message.delete()
        string = ""
        for word in message:
            string += f"{word} "
        await ctx.send(string)
    
    @commands.guild_only()
    @commands.command(pass_context=True)
    async def moveall(self, ctx: commands.Context):
        await ctx.message.delete()
        if ctx.message.author.voice is None:
            embed = discord.Embed(colour=0xff0000, title=f"You are not in a voice channel")
            await ctx.send(embed=embed)
            return
        channel = ctx.message.author.voice.channel
        guild = ctx.guild
        async for member in guild.fetch_members(limit=None):
            if member.id != ctx.message.author.id and not member.voice is None:
                member.move_to(channel)
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title=f"I moved everyone to {channel.name}")
        await ctx.send(embed=embed)