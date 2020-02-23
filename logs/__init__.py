from .logs import LOGS

async def setup(bot):
    bot.add_cog(LOGS(bot))