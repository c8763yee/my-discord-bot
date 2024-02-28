import datetime
import json
import os
import re
from textwrap import dedent
from typing import Optional

import discord
from aiomqtt import Client
from dotenv import load_dotenv

from cogs import CogsExtension, Field
from loggers import setup_package_logger

if os.path.exists('env/mqtt.env'):
    load_dotenv('env/mqtt.env', verbose=True, override=True)

MQTT_BROKER: str = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT: int = int(os.getenv('MQTT_PORT', 1883))


logger = setup_package_logger(__name__)


class KasaUtils(CogsExtension):
    async def get_power_usage(self, plug_id: int) -> discord.Embed:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.subscribe(
                f"hs300/emeter{('/%d' % plug_id) if plug_id != 0 else ''}"
            )
            async for message in client.messages:  # we only need the 1st message
                payload = json.loads(message.payload)
                break

        embed = await self.create_embed(
            "Power Usage Report",
            f"Power usage of the plug: {payload['name']}(ID: {plug_id})",
            discord.Color.green(
            ) if payload["is_on"] else discord.Color.blurple(),
            None,
            None,
            Field(name="Total Energy(kWh)",
                  value=payload["total_wh"], inline=False),
            Field(name="Voltage(V)", value=payload["V"]),
            Field(name="Current(A)", value=payload["A"]),
            Field(name="Power(W)", value=payload["W"]),
        )
        return embed

    async def turn_on(self, plug_id: int) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(f"hs300/command/on/{plug_id}", b"", qos=1)
        return f"Turned on plug {plug_id}"

    async def turn_off(self, plug_id: int) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(f"hs300/command/off/{plug_id}", b"", qos=1)
        return f"Turned off plug {plug_id}"

    async def toggle(self, plug_id: int, status: Optional[str] = None) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(f"hs300/command/toggle/{plug_id}", json.dumps({"status": status}).encode(), qos=1)

        return f"Toggled plug {plug_id}"
