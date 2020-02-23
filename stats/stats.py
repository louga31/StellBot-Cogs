import concurrent.futures
import functools
from datetime import datetime, timedelta
import asyncio
import locale
from dateutil.relativedelta import relativedelta
from redbot.core import Config, commands
from redbot.core.data_manager import cog_data_path
import discord
import apsw

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

class Stats(commands.Cog):
    """Stats"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 15646546161512)
        self._connection = apsw.Connection(str(cog_data_path(self) / 'stats.db'))
        self.cursor = self._connection.cursor()
        self.cursor.execute('PRAGMA journal_mode = wal;')
        self.cursor.execute('PRAGMA read_uncommitted = 1;')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS member_stats ('
            'user_id INTEGER NOT NULL,'
            'message_quantity INTEGER DEFAULT 1,'
            'voice_time INTEGER DEFAULT 1,'
            'joined_voice_time INTEGER DEFAULT 1,'
            'PRIMARY KEY (user_id)'
            ');'
        )
        self._executor = concurrent.futures.ThreadPoolExecutor(1)
        self.time = int(((datetime.now().replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1))-datetime.now()).total_seconds())
        self.task = self.bot.loop.create_task(self.cleanup_db())

    @commands.command(pass_context=True)
    async def stats(self, ctx):
        """Affiche les statistiques d'un utilisateur"""
        users = ctx.message.mentions
        for k in users:
            em = discord.Embed(description='Stats of <@' + str(k.id) +'>', colour=0x00ff40)
            em.set_thumbnail(url=k.avatar_url)
            em.add_field(name='Nom', value=k.nick, inline=True)
            em.add_field(name='Status', value=k.status, inline=True)
            em.add_field(name="Date de création du compte", value=k.created_at.__format__('%A %d %B %Y à %H:%M:%S'))
            em.add_field(name="Date d'arrivée sur le serveur", value=k.joined_at.__format__('%A %d %B %Y à %H:%M:%S'))
            await ctx.send(embed=em)

    @commands.command(pass_context=True)
    async def stats_admin(self, ctx):
        """Affiche les statistiques d'un utilisateur"""
        users = ctx.message.mentions
        for k in users:
            result = self.cursor.execute(
                'SELECT message_quantity, voice_time FROM member_stats '
                'WHERE user_id = ?',
                [k.id]
            ).fetchall()
            if not result:
                return await ctx.send('This user have no stats yet')
            em = discord.Embed(description='Stats of <@' + str(k.id) +'>', colour=0x00ff40)
            em.set_thumbnail(url=k.avatar_url)
            em.add_field(name='Nom', value=k.nick, inline=True)
            em.add_field(name='Status', value=k.status, inline=True)
            em.add_field(name="Date de création du compte", value=k.created_at.__format__('%A %d %B %Y à %H:%M:%S'))
            em.add_field(name="Date d'arrivée sur le serveur", value=k.joined_at.__format__('%A %d %B %Y à %H:%M:%S'), inline=False)
            em.add_field(name="Messages envoyés", value=result[0][0], inline=True)
            em.add_field(name="Temps passé en vocal", value=timedelta(seconds=result[0][1]), inline=True)
            
            await ctx.send(embed=em)

    def cog_unload(self):
        self._executor.shutdown()
        if self.task:
            self.task.cancel()

    async def cleanup_db(self):
        """Loop task that sends reminders."""
        await self.bot.wait_until_ready()
        while self.bot.get_cog("Stats") == self:
            await asyncio.sleep(self.time)
            self.time = int(((datetime.now().replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1))-datetime.now()).total_seconds())
            query = (
                'DELETE FROM member_stats'
            )
            data = []
            task = functools.partial(self.safe_write, query, data)
            await self.bot.loop.run_in_executor(self._executor, task)

    def safe_write(self, query, data):
        """Func for safely writing in another thread."""
        cursor = self._connection.cursor()
        cursor.execute(query, data)

    @commands.Cog.listener()
    async def on_message_without_command(self, msg):
        """Passively records all message contents."""
        if not msg.author.bot and isinstance(msg.channel, discord.TextChannel):
            query = (
                'INSERT INTO member_stats (user_id, voice_time, joined_voice_time)'
                'VALUES (?, 0, 0)'
                'ON CONFLICT(user_id) DO UPDATE SET message_quantity = message_quantity + 1;'
            )
            data = [msg.author.id]
            task = functools.partial(self.safe_write, query, data)
            await self.bot.loop.run_in_executor(self._executor, task)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Passively records all voice activity."""
        if not member.bot:
            if (before.channel is None) and not (after.channel is None):
                query = (
                    'INSERT INTO member_stats (user_id, message_quantity, joined_voice_time)'
                    'VALUES (?, 0, ?)'
                    'ON CONFLICT(user_id) DO UPDATE SET joined_voice_time = ?;'
                )
                now = datetime.now()
                data = [member.id, datetime.timestamp(now), datetime.timestamp(now)]
                task = functools.partial(self.safe_write, query, data)
                await self.bot.loop.run_in_executor(self._executor, task)
            elif not (before.channel is None) and (after.channel is None):
                result = self.cursor.execute(
                    'SELECT joined_voice_time FROM member_stats '
                    'WHERE user_id = ?',
                    [member.id]
                ).fetchall()
                if not result or result[0][0] == 0:
                    return
                joined_voice_time = datetime.fromtimestamp(result[0][0])
                query = (
                    'INSERT INTO member_stats (user_id, message_quantity, voice_time, joined_voice_time)'
                    'VALUES (?, 0, ?, 0)'
                    'ON CONFLICT(user_id) DO UPDATE SET voice_time = message_quantity + ?;'
                )
                now = datetime.now()
                time = round((now-joined_voice_time).total_seconds())
                data = [member.id, time, time]
                task = functools.partial(self.safe_write, query, data)
                await self.bot.loop.run_in_executor(self._executor, task)