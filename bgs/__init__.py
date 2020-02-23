from .bgs import BGS

async def setup(bot):
    bot.add_cog(BGS(bot))