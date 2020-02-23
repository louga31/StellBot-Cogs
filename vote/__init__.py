from .vote import Vote


def setup(bot):
    bot.add_cog(Vote(bot))
