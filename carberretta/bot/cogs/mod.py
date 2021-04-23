"""
MOD

Handles automatic mod systems:
    Mention-spam preventer;
    Modmail system;
    Nicknames;
    Profanity filter.

**Manual moderation is handled by Solaris, and thus is not included.**
"""

import datetime as dt
import string
import typing as t
from collections import defaultdict

import discord
from discord.ext import commands

from carberretta import Config
from carberretta.utils import chron
from carberretta.utils.emoji import UNICODE_EMOJI


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.modmail_cooldown: defaultdict = defaultdict(dt.datetime.utcnow)

        self.nickname_whitelist = set(
            string.ascii_letters
            + string.digits
            + string.punctuation.replace("@", " ")
            + "".join(UNICODE_EMOJI)
            + "áàȧâäǟǎăāãåǻǽǣćċĉčďḍḑḓéèėêëěĕēẽe̊ẹǵġĝǧğg̃ģĥḥíìiîïǐĭīĩịĵķǩĺļľŀḽm̂m̄ŉńn̂ṅn̈ňn̄ñņṋóòôȯȱöȫǒŏōõȭőọǿơp̄ŕřŗśŝṡšşṣťțṭṱúùûüǔŭūũűůụẃẁŵẅýỳŷÿȳỹźżžẓǯÁÀȦÂÄǞǍĂĀÃÅǺǼǢĆĊĈČĎḌḐḒÉÈĖÊËĚĔĒẼE̊ẸǴĠĜǦĞG̃ĢĤḤÍÌİÎÏǏĬĪĨỊĴĶǨĹĻĽĿḼM̂M̄ʼNŃN̂ṄN̈ŇN̄ÑŅṊÓÒȮȰÔÖȪǑŎŌÕȬŐỌǾƠP̄ŔŘŖŚŜṠŠȘṢŤȚṬṰÚÙÛÜǓŬŪŨŰŮỤẂẀŴẄÝỲŶŸȲỸŹŻŽẒǮæɑꞵðǝəɛɣıɩŋœɔꞷʊĸßʃþʋƿȝʒʔÆⱭꞴÐƎƏƐƔIƖŊŒƆꞶƱK’ẞƩÞƲǷȜƷʔąa̧ą̊ɓçđɗɖęȩə̧ɛ̧ƒǥɠħɦįi̧ɨɨ̧ƙłm̧ɲǫo̧øơɔ̧ɍşţŧųu̧ưʉy̨ƴĄA̧Ą̊ƁÇĐƊƉĘȨƏ̧Ɛ̧ƑǤƓĦꞪĮI̧ƗƗ̧ƘŁM̧ƝǪO̧ØƠƆ̧ɌŞŢŦŲU̧ƯɄY̨Ƴ"
        )

    async def modmail(self, message: discord.Message) -> None:
        if (retry_after := (self.modmail_cooldown[message.author.id] - dt.datetime.utcnow()).total_seconds()) > 0:
            return await message.channel.send(
                f"You're still on cooldown. Try again in {chron.long_delta(dt.timedelta(seconds=retry_after))}."
            )

        if not 50 <= len(message.content) <= 1000:
            return await message.channel.send("Your message should be between 50 and 1,000 characters long.")

        member = self.bot.guild.get_member(message.author.id)

        await self.modmail_channel.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Modmail",
                    "color": member.colour.value,
                    "thumbnail": {"url": f"{member.avatar_url}"},
                    "footer": {"text": f"ID: {message.id}"},
                    "image": {"url": att[0].url if len((att := message.attachments)) else None},
                    "fields": [
                        {"name": "Member", "value": member.mention, "inline": False},
                        {"name": "Message", "value": message.content, "inline": False},
                    ],
                }
            )
        )
        await message.channel.send(
            "Message sent. If needed, a moderator will DM you regarding this issue. You'll need to wait 1 hour before sending another modmail."
        )
        self.modmail_cooldown[message.author.id] = dt.datetime.utcnow() + dt.timedelta(seconds=3600)

    async def unhoist(self, nickname: str) -> str:
        while nickname and nickname[0] not in string.ascii_letters:
            nickname = nickname[1:] if nickname[1:] else ""

        return " ".join(nickname.split(" "))

    async def nickname_valid(self, nickname: str) -> bool:
        return (
            set(nickname.replace(".", "", 1).replace(" ", "", 1)[:3]).issubset(set(string.ascii_letters))
            if nickname
            else False
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.modmail_channel = self.bot.get_channel(Config.MODMAIL_ID)
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.author.bot:
            if isinstance(message.channel, discord.DMChannel):
                await self.modmail(message)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if not after.bot and after.nick and before.nick != after.nick:
            try:
                nickname = await self.unhoist("".join(c for c in after.nick if c in self.nickname_whitelist))

                if await self.nickname_valid(nickname):
                    if nickname != after.nick:
                        await after.edit(nick=nickname, reason="Nickname contains invalid characters")
                else:
                    await after.edit(
                        nick=before.nick if await self.nickname_valid(before.nick) else None, reason="Invalid nickname"
                    )
            except discord.Forbidden:
                pass

    @commands.command(name="validatenicknames", aliases=["va"])
    @commands.has_permissions(manage_nicknames=True)
    async def validatenicknames_command(self, ctx):
        for member in ctx.guild.members:
            if not member.bot and member.nick:
                try:
                    nickname = await self.unhoist("".join(c for c in member.nick if c in self.nickname_whitelist))

                    if await self.nickname_valid(nickname):
                        if nickname != member.nick:
                            await member.edit(nick=nickname, reason="Nickname contains invalid characters")
                    else:
                        await member.edit(nick=None, reason="Invalid nickname")
                except discord.Forbidden:
                    pass
        await ctx.send("Done.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Mod(bot))
