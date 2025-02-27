# Copyright (c) 2020-2021, Carberra Tutorials
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import datetime as dt
import unicodedata

import hikari
import lightbulb

from carberretta.utils import helpers

plugin = lightbulb.Plugin("Text")


@plugin.command
@lightbulb.option("characters", "The characters to get the information on.")
@lightbulb.command("charinfo", "Get character information.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_charinfo(ctx: lightbulb.SlashContext) -> None:
    characters = ctx.options.characters
    if len(characters) > 15:
        await ctx.respond("You can only pass 15 characters at a time.")
        return

    if not (member := ctx.member):
        return

    names = []
    points = []

    for c in characters:
        digit = f"{ord(c):x}".upper()
        name = unicodedata.name(c, "N/A")
        names.append(f"[{name}](https://fileformat.info/info/unicode/char/{digit})")
        points.append(f"U+{digit:>04}")

    await ctx.respond(
        hikari.Embed(
            title="Character information",
            description=f"Displaying information on {len(characters)} character(s).",
            colour=helpers.choose_colour(),
            timestamp=dt.datetime.now().astimezone(),
        )
        .set_author(name="Query")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .add_field("Names", "\n".join(names), inline=True)
        .add_field("Code points", "\n".join(points), inline=True)
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
