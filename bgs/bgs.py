from redbot.core import commands, checks, Config
import contextlib
import functools
from typing import Union, Iterable, Optional, Callable, ClassVar, List, Pattern, Sequence, Tuple, cast
import discord.utils
import discord
import locale
from datetime import datetime, timedelta
import asyncio, aiohttp
from threading import Thread
import math
from bs4 import BeautifulSoup
locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
default_settings = {
    "FACTIONS": [],
    "VALUES": [],
    "TIMES": [],
}

_ReactableEmoji = Union[str, discord.Emoji]

async def menu(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message = None,
    page: int = 0,
    timeout: float = 86400.0,
):
    """
    An emoji-based menu

    .. note:: All pages should be of the same type

    .. note:: All functions for handling what a particular emoji does
              should be coroutines (i.e. :code:`async def`). Additionally,
              they must take all of the parameters of this function, in
              addition to a string representing the emoji reacted with.
              This parameter should be the last one, and none of the
              parameters in the handling functions are optional

    Parameters
    ----------
    ctx: commands.Context
        The command context
    pages: `list` of `str` or `discord.Embed`
        The pages of the menu.
    controls: dict
        A mapping of emoji to the function which handles the action for the
        emoji.
    message: discord.Message
        The message representing the menu. Usually :code:`None` when first opening
        the menu
    page: int
        The current page number of the menu
    timeout: float
        The time (in seconds) to wait for a reaction

    Raises
    ------
    RuntimeError
        If either of the notes above are violated
    """
    if not all(isinstance(x, discord.Embed) for x in pages) and not all(
        isinstance(x, str) for x in pages
    ):
        raise RuntimeError("All pages must be of the same type")
    for key, value in controls.items():
        maybe_coro = value
        if isinstance(value, functools.partial):
            maybe_coro = value.func
        if not asyncio.iscoroutinefunction(maybe_coro):
            raise RuntimeError("Function must be a coroutine")
    current_page = pages[page]

    if not message:
        if isinstance(current_page, discord.Embed):
            message = await ctx.send(embed=current_page)
        else:
            message = await ctx.send(current_page)
        # Don't wait for reactions to be added (GH-1797)
        # noinspection PyAsyncCall
        start_adding_reactions(message, controls.keys(), ctx.bot.loop)
    else:
        try:
            if isinstance(current_page, discord.Embed):
                await message.edit(embed=current_page)
            else:
                await message.edit(content=current_page)
        except discord.NotFound:
            return

    try:
        react, user = await ctx.bot.wait_for(
            "reaction_add",
            check=ReactionPredicate.with_emojis(tuple(controls.keys()), message, ctx.author),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        try:
            await message.clear_reactions()
        except discord.Forbidden:  # cannot remove all reactions
            for key in controls.keys():
                await message.remove_reaction(key, ctx.bot.user)
        except discord.NotFound:
            return
    else:
        return await controls[react.emoji](
            ctx, pages, controls, message, page, timeout, react.emoji, user
        )


async def next_page(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
    user: str,
):
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, user)
    if page == len(pages) - 1:
        page = 0  # Loop around to the first item
    else:
        page = page + 1
    return await menu(ctx, pages, controls, message=message, page=page, timeout=timeout)


async def prev_page(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
    user: str,
):
    perms = message.channel.permissions_for(ctx.me)
    if perms.manage_messages:  # Can manage messages, so remove react
        with contextlib.suppress(discord.NotFound):
            await message.remove_reaction(emoji, user)
    if page == 0:
        page = len(pages) - 1  # Loop around to the last item
    else:
        page = page - 1
    return await menu(ctx, pages, controls, message=message, page=page, timeout=timeout)


async def close_menu(
    ctx: commands.Context,
    pages: list,
    controls: dict,
    message: discord.Message,
    page: int,
    timeout: float,
    emoji: str,
    user: str,
):
    with contextlib.suppress(discord.NotFound):
        await message.delete()


def start_adding_reactions(
    message: discord.Message,
    emojis: Iterable[_ReactableEmoji],
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> asyncio.Task:
    """Start adding reactions to a message.

    This is a non-blocking operation - calling this will schedule the
    reactions being added, but the calling code will continue to
    execute asynchronously. There is no need to await this function.

    This is particularly useful if you wish to start waiting for a
    reaction whilst the reactions are still being added - in fact,
    this is exactly what `menu` uses to do that.

    This spawns a `asyncio.Task` object and schedules it on ``loop``.
    If ``loop`` omitted, the loop will be retrieved with
    `asyncio.get_event_loop`.

    Parameters
    ----------
    message: discord.Message
        The message to add reactions to.
    emojis : Iterable[Union[str, discord.Emoji]]
        The emojis to react to the message with.
    loop : Optional[asyncio.AbstractEventLoop]
        The event loop.

    Returns
    -------
    asyncio.Task
        The task for the coroutine adding the reactions.

    """

    async def task():
        # The task should exit silently if the message is deleted
        with contextlib.suppress(discord.NotFound):
            for emoji in emojis:
                await message.add_reaction(emoji)

    if loop is None:
        loop = asyncio.get_event_loop()

    return loop.create_task(task())


DEFAULT_CONTROLS = {"⬅": prev_page, "❌": close_menu, "➡": next_page}

class ReactionPredicate(Callable[[discord.Reaction, discord.abc.User], bool]):
    """A collection of predicates for reaction events.

    All checks are combined with :meth:`ReactionPredicate.same_context`.

    Examples
    --------
    Confirming a yes/no question with a tick/cross reaction::

        from redbot.core.utils.predicates import ReactionPredicate
        from redbot.core.utils.menus import start_adding_reactions

        msg = await ctx.send("Yes or no?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result is True:
            # User responded with tick
            ...
        else:
            # User responded with cross
            ...

    Waiting for the first reaction from any user with one of the first
    5 letters of the alphabet::

        from redbot.core.utils.predicates import ReactionPredicate
        from redbot.core.utils.menus import start_adding_reactions

        msg = await ctx.send("React to me!")
        emojis = ReactionPredicate.ALPHABET_EMOJIS[:5]
        start_adding_reactions(msg, emojis)

        pred = ReactionPredicate.with_emojis(emojis, msg)
        await ctx.bot.wait_for("reaction_add", check=pred)
        # pred.result is now the index of the letter in `emojis`

    Attributes
    ----------
    result : Any
        The object which the message content matched with. This is
        dependent on the predicate used - see each predicate's
        documentation for details, not every method will assign this
        attribute. Defaults to ``None``.

    """

    YES_OR_NO_EMOJIS: ClassVar[Tuple[str, str]] = (
        "\N{WHITE HEAVY CHECK MARK}",
        "\N{NEGATIVE SQUARED CROSS MARK}",
    )
    """Tuple[str, str] : A tuple containing the tick emoji and cross emoji, in that order."""

    ALPHABET_EMOJIS: ClassVar[List[str]] = [
        chr(code)
        for code in range(
            ord("\N{REGIONAL INDICATOR SYMBOL LETTER A}"),
            ord("\N{REGIONAL INDICATOR SYMBOL LETTER Z}") + 1,
        )
    ]
    """List[str] : A list of all 26 alphabetical letter emojis."""

    NUMBER_EMOJIS: ClassVar[List[str]] = [
        chr(code) + "\N{COMBINING ENCLOSING KEYCAP}" for code in range(ord("0"), ord("9") + 1)
    ]
    """List[str] : A list of all single-digit number emojis, 0 through 9."""

    def __init__(
        self, predicate: Callable[["ReactionPredicate", discord.Reaction, discord.abc.User], bool]
    ) -> None:
        self._pred: Callable[
            ["ReactionPredicate", discord.Reaction, discord.abc.User], bool
        ] = predicate
        self.result = None

    def __call__(self, reaction: discord.Reaction, user: discord.abc.User) -> bool:
        return self._pred(self, reaction, user)

    # noinspection PyUnusedLocal
    @classmethod
    def same_context(
        cls, message: Optional[discord.Message] = None, user: Optional[discord.abc.User] = None
    ) -> "ReactionPredicate":
        """Match if a reaction fits the described context.

        This will ignore reactions added by the bot user, regardless
        of whether or not ``user`` is supplied.

        Parameters
        ----------
        message : Optional[discord.Message]
            The message which we expect a reaction to. If unspecified,
            the reaction's message will be ignored.
        user : Optional[discord.abc.User]
            The user we expect to react. If unspecified, the user who
            added the reaction will be ignored.

        Returns
        -------
        ReactionPredicate
            The event predicate.

        """
        # noinspection PyProtectedMember
        me_id = message._state.self_id
        return cls(
            lambda self, r, u: u.id != me_id
            and (message is None or r.message.id == message.id)
        )

    @classmethod
    def with_emojis(
        cls,
        emojis: Sequence[Union[str, discord.Emoji, discord.PartialEmoji]],
        message: Optional[discord.Message] = None,
        user: Optional[discord.abc.User] = None,
    ) -> "ReactionPredicate":
        """Match if the reaction is one of the specified emojis.

        Parameters
        ----------
        emojis : Sequence[Union[str, discord.Emoji, discord.PartialEmoji]]
            The emojis of which one we expect to be reacted.
        message : discord.Message
            Same as ``message`` in :meth:`same_context`.
        user : Optional[discord.abc.User]
            Same as ``user`` in :meth:`same_context`.

        Returns
        -------
        ReactionPredicate
            The event predicate.

        """
        same_context = cls.same_context(message, user)

        def predicate(self: ReactionPredicate, r: discord.Reaction, u: discord.abc.User):
            if not same_context(r, u):
                return False

            try:
                self.result = emojis.index(r.emoji)
            except ValueError:
                return False
            else:
                return True

        return cls(predicate)

    @classmethod
    def yes_or_no(
        cls, message: Optional[discord.Message] = None, user: Optional[discord.abc.User] = None
    ) -> "ReactionPredicate":
        """Match if the reaction is a tick or cross emoji.

        The emojis used can are in
        `ReactionPredicate.YES_OR_NO_EMOJIS`.

        This will assign ``True`` for *yes*, or ``False`` for *no* to
        the `result` attribute.

        Parameters
        ----------
        message : discord.Message
            Same as ``message`` in :meth:`same_context`.
        user : Optional[discord.abc.User]
            Same as ``user`` in :meth:`same_context`.

        Returns
        -------
        ReactionPredicate
            The event predicate.

        """
        same_context = cls.same_context(message, user)

        def predicate(self: ReactionPredicate, r: discord.Reaction, u: discord.abc.User) -> bool:
            if u.bot:
                return False
            if not same_context(r, u):
                return True

            try:
                self.result = not bool(self.YES_OR_NO_EMOJIS.index(r.emoji))
            except ValueError:
                return False
            else:
                return True

        return cls(predicate)

class BGS(commands.Cog):
    """BGS"""

    def __init__(self, bot):
        self.config = Config.get_conf(self, 175217614706966528)
        self.config.register_global(**default_settings)
        self.bgs_auto_loop = asyncio.new_event_loop()
        self.bot = bot
        self.stopped = False

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def get_system_data(self, session, link):
        async with session.get(link) as page:
            if page.status == 200:
                soup = BeautifulSoup(await page.text(), 'html.parser')
                table = soup.find('table', attrs={'class': 'tablesorter'})
                rows = table.findAll('tr')
                rows = rows[1:]
                factions = []
                percents = []
                infos = []
                for row in rows:
                    name = row.find_next('td').find_next('a').text
                    factions.append(name)
                    percent = row.find_next('td', attrs={'class': 'alignright'}).text
                    percents.append(percent)
                    active = row.find_all('td')[4]
                    infos_temp = active.findChildren('span')
                    for info in infos_temp:
                        infos.append(info.text)
                    infos.append('end')
                return(factions, percents, infos)

    async def bgs_auto(self, ctx, *, page: int = 1):
        """Affiche les stats BGS"""
        em = discord.Embed(title='The Wolf Society', description="Chargement des données BGS", colour=0x0E82AF)
        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
        message = await ctx.send(embed=em)
        bgs_loop = asyncio.new_event_loop()
        t = Thread(target=self.start_loop, args=(bgs_loop,))
        t.setDaemon(True)
        t.start()
        async def _bgs_menu(
            ctx: commands.Context,
            pages: list,
            controls: dict,
            message: discord.Message,
            page: int,
            timeout: float,
            emoji: str,
        ):
            if message:
                await ctx.send_help(self.bgs)
                await message.delete()
                return None
                
        quote_page = "https://inara.cz/galaxy-minorfaction/36276/"
        async with aiohttp.ClientSession() as session:
            async with session.get(quote_page) as pages:
                if pages.status == 200:
                    soup = BeautifulSoup(await pages.text(), 'html.parser')
                    table = soup.find('table', attrs={'class': 'tablesorter'})
                    rows = table.findAll('tr')
                    rows = rows[1:]
                    BGS_CONTROLS = {"⬅": prev_page, "➡": next_page}
                    len_bgs_pages = math.ceil(len(rows) / 4)
                    bgs_page_list = []
                    date = datetime.now()
                    factions_save = []
                    values_save = []
                    error = False
                    for page_num in range(1, len_bgs_pages + 1):
                        future = asyncio.run_coroutine_threadsafe(self._build_bgs_page(ctx, page_num, rows, date, factions_save, values_save, message), bgs_loop)
                        (embed, error, factions_save, values_save) = future.result()
                        if error:
                            return
                        bgs_page_list.append(embed)
                    bgs_loop.stop()
                    await self.config.FACTIONS.set(factions_save)
                    await self.config.VALUES.set(values_save)
                    if page > len_bgs_pages:
                        page = 1
                    await message.delete()
                    await menu(ctx, bgs_page_list, BGS_CONTROLS, page=(page - 1))
                elif page.status == 503:
                    em = discord.Embed(title='The Wolf Society', description="Limites de connexions de Inara dépassées", colour=0xFF0000)
                    em.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/France_road_sign_B1.svg/1200px-France_road_sign_B1.svg.png")
                    await message.edit(embed=em)

    async def _build_bgs_page(self, ctx, page_num, rows, date, factions_save, values_save, message):
        async with aiohttp.ClientSession() as session:
            bgs_num_pages = math.ceil(len(rows) / 4)
            bgs_idx_start = (page_num - 1) * 4
            bgs_idx_end = bgs_idx_start + 4
            em = discord.Embed(title='Infos BGS du {}'.format(date.__format__('%A %d %B %Y à %H:%M:%S')), description="Stats de la Wolf Society", colour=0x00ff40)
            em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
            footer = "Page {page_num}/{total_pages}".format(
                page_num=page_num,
                total_pages=bgs_num_pages,
            )
            em.set_footer(text=footer)
            war = discord.utils.get(ctx.message.guild.emojis, name="war")
            boom = discord.utils.get(ctx.message.guild.emojis, name="boom")
            retreat = discord.utils.get(ctx.message.guild.emojis, name="retreat")
            outbreak = discord.utils.get(ctx.message.guild.emojis, name="outbreak")
            Arrow_Up = discord.utils.get(ctx.message.guild.emojis, name="Arrow_Up")
            Arrow_Horizontal = discord.utils.get(ctx.message.guild.emojis, name="Arrow_Horizontal")
            Arrow_Down = discord.utils.get(ctx.message.guild.emojis, name="Arrow_Down")
            factions_load = await self.config.FACTIONS()
            values_load = await self.config.VALUES()
            for row in rows[bgs_idx_start:bgs_idx_end]:
                name = row.find_next('td').find_next('a').text
                updated = row.findAll('td', attrs={'class': 'minor'})[1].text
                link = 'https://inara.cz/' + row.find_next('td').find_next('a').get('href')
                try:
                    (factions, percents, infos) = await self.get_system_data(session, link)
                except Exception as e:
                    em = discord.Embed(title='The Wolf Society', description="Limites de connexions de Inara dépassées", colour=0xFF0000)
                    em.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/France_road_sign_B1.svg/1200px-France_road_sign_B1.svg.png")
                    await message.edit(embed=em)
                    print(e)
                    return (em, True, [], [])
                system_in_save = False
                if name in factions_load:
                    system_index = factions_load.index(name)
                    system_in_save = True
                    factions_data = factions_load[system_index+2:system_index+factions_load[system_index+1]+2]
                    values_data = values_load[system_index+2:system_index+values_load[system_index+1]+2]
                factions_save.append(name)
                factions_save.append(len(factions))
                values_save.append(name)
                values_save.append(len(factions))
                factions_text = ""
                for k in range(0, len(factions)):
                    infos_temp = []
                    for index1, info in enumerate(infos):
                        if info == 'end':
                            infos = infos[index1+1:]
                            break
                        infos_temp.append(info)
                    if system_in_save:
                        if factions[k] in factions_data:
                            index2 = factions_data.index(factions[k])
                            value_temp = float(values_data[index2][:-1])
                        if float(percents[k][:-1]) < value_temp:
                            factions_text += f' {Arrow_Down}'
                        elif float(percents[k][:-1]) == value_temp:
                            factions_text += f' {Arrow_Horizontal}'
                        elif float(percents[k][:-1]) > value_temp:
                            factions_text += f' {Arrow_Up}'
                    factions_text += factions[k] + ': ' + percents[k]
                    for info in infos_temp:
                        if info == 'War': 
                            factions_text += f' {war}'
                        elif info == 'Boom': 
                            factions_text += f' {boom}'
                        elif info == 'Retreat': 
                            factions_text += f' {retreat}'
                        elif info == 'Outbreak': 
                            factions_text += f' {outbreak}'
                    factions_text += '\n'
                    factions_save.append(factions[k])
                    values_save.append(percents [k])
                em.add_field(name=name + ': ' + updated, value=factions_text, inline=False)
            return(em, False, factions_save, values_save)

    @commands.group(name="bgs")
    async def bgs(self, ctx):
        """Commande principale du bgs"""
        await ctx.message.delete()
        pass
    
    @bgs.command(pass_context=True)
    async def now(self, ctx, *, page: int = 1):
        """Affiche les stats BGS"""
        await self.bgs_auto(ctx, page=page)

    async def bgs_sleep(self, ctx, secs):
        try:
            await asyncio.sleep(secs)
        except:
            await ctx.send("stopped")
            return

    @bgs.command(pass_context=True)
    async def start(self, ctx):
        """Lance les commandes BGS programmées (A finir)"""
        self.stopped = False
        while not self.stopped:
            while not self.stopped:
                times = await self.config.TIMES()
                time = times[0]
                time_temp = datetime.fromtimestamp(time)
                x=datetime.now()
                if time_temp <= x:
                    times[0] = datetime.timestamp(time_temp + timedelta(days=1))
                    times.sort()
                    await self.config.TIMES.set(times)
                    time = times[0]
                    time_temp = datetime.fromtimestamp(time)
                    break
                if not self.stopped:
                    delta_t=time_temp-x
                    secs=delta_t.total_seconds()
                    em = discord.Embed(title='The Wolf Society', description="BGS programmée le ``{}``".format(time_temp.__format__('%A %d %B %Y à %H:%M:%S')), colour=0x0E82AF)
                    em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
                    message = await ctx.send(embed=em)
                    await self.bgs_sleep(ctx, secs)
                    await message.delete()
                    times = await self.config.TIMES()
                    times[0] = datetime.timestamp(time_temp + timedelta(days=1))
                    times.sort()
                    await self.config.TIMES.set(times)
                    if not self.stopped:
                        await self.bgs_auto(ctx)
                    else:
                        await ctx.send("Boucle stoppé")
                        await ctx.send(self.stopped)
                        return
                else:
                    await ctx.send("Boucle stoppé")
                    await ctx.send(self.stopped)
                    return
            await ctx.send("Boucle stoppé")
            await ctx.send(self.stopped)
        await ctx.send("Boucle stoppé")
        await ctx.send(self.stopped)

    @bgs.command(pass_context=True)
    async def stop(self, ctx):
        """Stoppe les commandes BGS programmées"""
        em = discord.Embed(title='The Wolf Society', description="Commandes BGS Stoppées", colour=0xFF0000)
        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
        await ctx.send(embed=em)
        self.stopped = True

    @bgs.command(pass_context=True)
    async def add(self, ctx, heure, *, minutes: int = 0, secondes: int = 0):
        """Ajoute une heure à la liste BGS programmée"""
        times = await self.config.TIMES()
        time = datetime.today()
        time = time.replace(hour=int(heure), minute=minutes, second=secondes, microsecond=0)
        if time < datetime.now():
            time += timedelta(days=1)
        if times != None:
            times.append(datetime.timestamp(time))
            times.sort()
        else:
            times = [datetime.timestamp(time)]
        await self.config.TIMES.set(times)
        time_text = "**{}**".format(time.__format__('%H:%M:%S'))
        em = discord.Embed(title='The Wolf Society', description=f"Horaire ajouté\n{time_text}", colour=0x0E82AF)
        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
        await ctx.send(embed=em)

    @bgs.command(pass_context=True)
    async def remove(self, ctx, id):
        """Retire une heure à la liste BGS programmée"""
        times = await self.config.TIMES()
        try:
            times.pop(int(id)-1)
            await self.config.TIMES.set(times)
            time = datetime.fromtimestamp(times[int(id)-1])
            time_text = "**{}**".format(time.__format__('%H:%M:%S'))
            em = discord.Embed(title='The Wolf Society', description=f"Horaire supprimé\n{time_text}", colour=0x0E82AF)
            em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
            await ctx.send(embed=em)
        except:
            em = discord.Embed(title='The Wolf Society', description="Horaire inexistant", colour=0xFF0000)
            em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
            await ctx.send(embed=em)
    
    @bgs.command(pass_context=True)
    async def clean(self, ctx):
        """Retire les heures de la liste BGS programmée"""
        await self.config.TIMES.set([])
        em = discord.Embed(title='The Wolf Society', description="Horaires supprimés", colour=0x0E82AF)
        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
        await ctx.send(embed=em)
    
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    @bgs.command(pass_context=True)
    async def list(self, ctx, *, page: int = 1):
        """Liste les heures BGS programmées"""
        times = await self.config.TIMES()
        if len(times) == 0:
            em = discord.Embed(title='The Wolf Society', description="Aucuns horaires définis", colour=0xFF0000)
            em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
            await ctx.send(embed=em)
            return
        async def _list_menu(
            ctx: commands.Context,
            pages: list,
            controls: dict,
            message: discord.Message,
            page: int,
            timeout: float,
            emoji: str,
        ):
            pass
        LIST_CONTROLS = {"⬅": prev_page, "❌": close_menu, "➡": next_page}
        len_list_pages = math.ceil(len(times) / 10)
        list_page_list = []
        for page_num in range(1, len_list_pages + 1):
            embed = await self._build_list_page(ctx, page_num, times)
            list_page_list.append(embed)
        if page > len_list_pages:
            page = 1
        await menu(ctx, list_page_list, LIST_CONTROLS, page=(page - 1))

    async def _build_list_page(self, ctx, page_num, times):
        list_num_pages = math.ceil(len(times) / 10)
        list_idx_start = (page_num - 1) * 10
        list_idx_end = list_idx_start + 10
        footer = "Page {page_num}/{total_pages}".format(
            page_num=page_num,
            total_pages=list_num_pages,
        )
        desc = "Liste des heures BGS\n"
        for i, time in enumerate(times[list_idx_start:list_idx_end], start=list_idx_start):
            time_temp = datetime.fromtimestamp(time)
            list_idx = i+1
            time_text = "{}".format(time_temp.__format__('%A %d %B %Y à %H:%M:%S'))
            desc += f"`{list_idx}.` **{time_text}**\n"
        em = discord.Embed(title='The Wolf Society', description=desc, colour=0x0E82AF)
        em.set_thumbnail(url="https://cdn.discordapp.com/attachments/432524913132437514/607970978722742283/logo-wolf.png")
        em.set_footer(text=footer)
        return em