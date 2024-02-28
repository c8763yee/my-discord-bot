from typing import Literal, Optional

import discord
from discord.ext import commands

from loggers import setup_package_logger

from .tasks import KasaTasks
from .utils import KasaUtils

logger = setup_package_logger(__name__)


class KasaCMD(KasaTasks):
    # variables
    def __init__(self, bot):
        super().__init__(bot)
        self.utils = KasaUtils(bot)

    # methods(commands)
    @commands.hybrid_group(ephermal=True)
    async def kasa(self, ctx: commands.Context):
        logger.debug("kasa command invoked.")

    @kasa.command("emeter")
    async def kasa_emeter(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        embed = await self.utils.get_power_usage(plug_id)
        await ctx.send(embed=embed)

    @kasa.command("emeters")
    async def kasa_emeters(self, ctx: commands.Context, plug_ids: commands.Greedy[commands.Range[int, 0, 6]] = None):
        if plug_ids is None:
            plug_ids = range(6+1)  # default to all plugs

        for plug_id in plug_ids:
            embed = await self.utils.get_power_usage(plug_id)
            await ctx.send(embed=embed)

    @kasa.command("on")
    async def kasa_on(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        await ctx.send(await self.utils.turn_on(plug_id))

    @kasa.command("off")
    async def kasa_off(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        await ctx.send(await self.utils.turn_off(plug_id))

    @kasa.command("toggle")
    async def kasa_toggle(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6], status: Optional[Literal["on", "off"]] = None):
        await ctx.send(await self.utils.toggle(plug_id, status))
