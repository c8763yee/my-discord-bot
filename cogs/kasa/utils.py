import json
import os
from collections.abc import Iterable
from pathlib import Path

import discord
from aiomqtt import Client
from dotenv import load_dotenv

from core.classes import BaseClassMixin
from core.models import Field

env_path = Path.cwd() / "env" / "mqtt.env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, verbose=True)

MQTT_BROKER: str = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.environ.get("MQTT_PORT", 1883))


class KasaUtils:
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


class KasaResponseFormatter(BaseClassMixin):
    @classmethod
    async def format_power_usage(cls, payload: dict) -> discord.Embed:
        return cls.create_embed(
            "Power Usage Report",
            f"Power usage of the plug: {payload['name']}(ID: {payload['id']})",
            Field(name="Total Energy(kWh)", value=payload["total_wh"]),
            Field(name="Voltage(V)", value=payload["V"]),
            Field(name="Current(A)", value=payload["A"]),
            Field(name="Power(W)", value=payload["W"]),
            color=(discord.Color.green() if payload["status"] else discord.Color.from_rgb(0, 0, 0)),
        )

    @classmethod
    async def format_power_usage_multiple(cls, payloads: dict) -> list[discord.Embed]:
        embeds = []
        for payload in payloads.values():
            embed = await cls.format_power_usage(payload)
            embeds.append(embed)

        return embeds
