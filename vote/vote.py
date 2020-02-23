import asyncio
import locale
import discord
from redbot.core import commands, Config
from redbot.core.bot import RedBase

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

listener = getattr(commands.Cog, "listener", None)  # red 3.0 backwards compatibility support

class Vote(commands.Cog):
    """Votes"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 4156164897498)
        self.votes = []
        asyncio.ensure_future(self.set_votes())

    async def set_votes(self):
        self.votes = await self.config.VOTES()

    async def get_colour(self, channel):
        return await RedBase.get_embed_colour(self.bot, channel)

    async def edit_vote(self, message, vote):
        votes = []
        description = []
        embed = message.embeds[0]
        unformatted_options = [x.strip() for x in embed.description.split('\n')]
        options_dict = vote['options']
        options = []
        for x in options_dict:
            options.append(x)
        for k in options:
            votes.append(0)
        for x, y in vote['voters'].items():
            if y != 'null':
                votes[options.index(y)] += 1
        for k in enumerate(votes):
            option = unformatted_options[k]
            option = option[:-6]
            option = option.split(' --- ')
            description += '\n {}'.format(option[0])
            description += ' --- ' + str(votes[k]) + ' votes'
        # ['{}: {}'.format(opt_dict[key], tally[key]) ]
        embed2 = discord.Embed(colour=embed.colour, title=embed.title, description=''.join(description))
        embed2.set_footer(text=embed.footer.text)
        await message.edit(embed=embed2)

    @listener()
    async def on_raw_reaction_add(self, payload):
        vote_message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if vote_message.author.id == payload.user_id:
            return
        if not vote_message.embeds:
            return
        embed = vote_message.embeds[0]
        try:
            if not embed.footer.text.startswith('Vote ID:'):
                return
        except:
            return
        for k in range(len(self.votes)):
            if self.votes[k]['id'] == str(vote_message.id):
                vote = self.votes[k]
                index = k
        voters = vote['voters']  # add the bot's ID to the list of voters to exclude it's votes
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if str(payload.user_id) in voters:
            await vote_message.remove_reaction(payload.emoji, member)
            voters.pop(str(payload.user_id))
        for x, y in vote['options'].items():
            if y == str(payload.emoji):
                option = x
        vote['voters'][str(payload.user_id)] = option
        self.votes[index] = vote
        await self.edit_vote(vote_message, vote)
        await vote_message.remove_reaction(payload.emoji, member)
        await self.config.VOTES.set(self.votes)

    @commands.guild_only()
    @commands.command(pass_context=True)
    async def vote(self, ctx):
        await ctx.message.delete()
        users = ctx.message.mentions
        for k in users:
            options = ["Oui", "Non", "Joker"]
            reactions = ['✅', '❌', '🃏']
            emoji = {"oui": "✅", "non": "❌", "joker": "🃏"}
            emojis = {}
            description = []
            votes = []
            for x, option in enumerate(options):
                emojis[list(emoji.keys())[x]] = emoji[list(emoji.keys())[x]]
                votes.append(0)
                description += '\n {} {}'.format(reactions[x], option)
                description += ' --- ' + str(votes[x]) + ' votes'
            embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title=f"Vote pour l'intégration de {k.nick}",
                                  description=''.join(description))
            react_message = await ctx.send(embed=embed)
            for reaction in reactions[:len(options)]:
                await react_message.add_reaction(reaction)
            embed.set_footer(text='Vote ID: {}'.format(react_message.id))
            await react_message.edit(embed=embed)
            voters = {f"{react_message.author.id}": "null"}
            self.votes.append({"id": f"{react_message.id}", "options": emojis, "voters": voters})
            await self.config.VOTES.set(self.votes)

    @commands.command(pass_context=True)
    async def vote_clean(self, ctx):
        await self.config.VOTES.set([])
        embed = discord.Embed(colour=await self.get_colour(ctx.message.channel), title="Votes cleaned")
        await ctx.send(embed=embed)
