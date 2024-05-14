from typing import Literal

from discord.ext import commands

from .tasks import KasaTasks
from .utils import KasaResponseFormatter


class KasaCMD(KasaTasks):
    # methods(commands)
    @commands.hybrid_group(ephermal=True)
    async def kasa(self, ctx: commands.Context):
        """
        dummy function to create a group command
        """

    @kasa.command("emeter")
    async def kasa_emeter(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        await ctx.interaction.response.defer()
        payload = await self.utils.get_power_usage(plug_id)
        embed = await KasaResponseFormatter.format_power_usage(payload)
        await ctx.send(f"Power usage of plug {plug_id}", embed=embed)

    @kasa.command("emeters")
    async def kasa_emeters(
        self,
        ctx: commands.Context,
        plug_ids: commands.Greedy[commands.Range[int, 0, 6]] = None,
    ):
        await ctx.interaction.response.defer()
        if plug_ids is None:
            plug_ids = range(6 + 1)  # default to all plugs

        payloads = await self.utils.get_power_usage_multiple(plug_ids)
        embeds = await KasaResponseFormatter.format_power_usage_multiple(payloads)
        await ctx.interaction.followup.send(
            f"Power usage of plugs ({', '.join(map(str, plug_ids))})", embeds=embeds
        )

    @commands.is_owner()
    @kasa.command("on")
    async def kasa_on(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        await ctx.send(await self.utils.turn_on(plug_id))

    @commands.is_owner()
    @kasa.command("off")
    async def kasa_off(self, ctx: commands.Context, plug_id: commands.Range[int, 0, 6]):
        await ctx.send(await self.utils.turn_off(plug_id))

    @commands.is_owner()
    @kasa.command("toggle")
    async def kasa_toggle(
        self,
        ctx: commands.Context,
        plug_id: commands.Range[int, 0, 6],
        status: Literal["on", "off"] | None = None,
    ):
        await ctx.send(await self.utils.toggle(plug_id, status))
