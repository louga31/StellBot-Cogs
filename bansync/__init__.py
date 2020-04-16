from .bansync import bansync

def setup(bot):
    bot.add_cog(bansync(bot))
