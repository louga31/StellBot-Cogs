from .safeclean import SafeClean


def setup(bot):
    n = SafeClean(bot)
    bot.add_cog(n)
    # bot.add_listener(n._roler, "on_member_join")
    # bot.add_listener(n._verify_json, "on_error")
