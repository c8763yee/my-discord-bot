import json
import os
from collections.abc import Iterable

import discord
from aiomqtt import Client
from dotenv import load_dotenv

from cogs import CogsExtension
from loggers import setup_package_logger

if os.path.exists("env/mqtt.env"):
    load_dotenv("env/mqtt.env", verbose=True, override=True)

MQTT_BROKER: str = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.environ.get("MQTT_PORT", 1883))


logger = setup_package_logger(__name__)


class KasaUtils(CogsExtension):
    async def get_power_usage(self, plug_id: int) -> dict:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            plug_url_suffix = f"/{plug_id}" if plug_id != 0 else ""
            await client.subscribe(f"hs300/emeter{plug_url_suffix}")
            async for message in client.messages:  # we only need the 1st message
                payload = {**json.loads(message.payload), "id": plug_id}
                break

        return payload

    async def get_power_usage_multiple(self, plug_ids: Iterable[int]) -> dict:
        payloads = {}
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            for plug_id in plug_ids:
                plug_url_suffix = f"/{plug_id}" if plug_id != 0 else ""
                await client.subscribe(f"hs300/emeter{plug_url_suffix}")
            async for message in client.messages:
                payload = json.loads(message.payload)
                topic = str(message.topic)
                id_num = 0 if topic == "hs300/emeter" else int(topic.rsplit("/", maxsplit=1)[-1])
                payloads[payload["name"]] = {**payload, "id": id_num}
                if len(payloads) == len(plug_ids):
                    break

        return dict(sorted(payloads.items(), key=lambda x: x[1]["id"]))

    async def turn_on(self, plug_id: int) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(f"hs300/command/on/{plug_id}", json.dumps({}).encode(), qos=1)
        return f"Turned on plug {plug_id}"

    async def turn_off(self, plug_id: int) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(f"hs300/command/off/{plug_id}", json.dumps({}).encode(), qos=1)
        return f"Turned off plug {plug_id}"

    async def toggle(self, plug_id: int, status: str | None = None) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(
                f"hs300/command/toggle/{plug_id}",
                json.dumps({"status": status}).encode(),
                qos=1,
            )

        return f"Toggled plug {plug_id}"


class KasaResponseFormatter:
    @classmethod
    async def format_power_usage(cls, payload: dict) -> discord.Embed:
        return (
            discord.Embed(
                title="Power Usage Report",
                description=f"Power usage of the plug: {payload['name']}(ID: {payload['id']})",
                color=(
                    discord.Color.green() if payload["is_on"] else discord.Color.from_rgb(0, 0, 0)
                ),
            )
            .add_field(name="Total Energy(kWh)", value=payload["total_wh"], inline=False)
            .add_field(name="Voltage(V)", value=payload["V"], inline=True)
            .add_field(name="Current(A)", value=payload["A"], inline=True)
            .add_field(name="Power(W)", value=payload["W"], inline=True)
        )

    @classmethod
    async def format_power_usage_multiple(cls, payloads: dict) -> list[discord.Embed]:
        embeds = []
        for payload in payloads.values():
            embed = await cls.format_power_usage(payload)
            embeds.append(embed)
        return embeds
