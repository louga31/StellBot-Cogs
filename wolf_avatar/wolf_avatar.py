import io
import locale

from PIL import Image

import discord
from redbot.core import commands

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

class Wolf_avatar(commands.Cog):
    """Stats"""

    @commands.command(pass_context=True)
    async def wolf_avatar(self, ctx):
        """Créé un avatar personnalisé en utilisant le cadre de la team"""
        for image in ctx.message.attachments:
            image_file = io.BytesIO(await image.read())
            frame = Image.open("/data/wolf_frame.png").resize((512, 512)).convert(mode="RGBA")
            avatarsrc = Image.open(image_file)
            (oldWidth, oldHeight) = avatarsrc.size
            avatarsrc = avatarsrc.resize((round(oldWidth/(max(oldWidth, oldHeight)/512)), round(oldHeight/(max(oldWidth, oldHeight)/512))))
            avatar = Image.new("RGBA", (512,512))
            (oldWidth, oldHeight) = avatarsrc.size
            avatar.paste(avatarsrc, (round((512-oldWidth)/2), round((512-oldHeight)/2)))
            final = Image.new("RGBA", frame.size)
            final = Image.alpha_composite(final, frame)
            final = Image.alpha_composite(final, avatar)
            avatar_file = io.BytesIO()
            final.save(avatar_file, format="PNG")
            avatar_file.seek(0)
            await ctx.send("Voici votre avatar customizé", file=discord.File(fp=avatar_file, filename="avatar.png"))
