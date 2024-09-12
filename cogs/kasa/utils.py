import datetime
import json
import os
from collections.abc import Iterable
from pathlib import Path

import discord
from aiomqtt import Client
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core import load_env
from core.classes import BaseClassMixin
from core.models import Field
from database import (
    HS300,
    Emeter,
    engine,
)

from .const import MQTTQoS, PlugID, plug_mapping

load_env(path=Path.cwd() / "env" / "mqtt.env")

MQTT_BROKER: str = os.environ.get("MQTT_BROKER", "localhost")  # use default mosquitto broker config
MQTT_PORT: int = int(os.environ.get("MQTT_PORT", 1883))

TZ = datetime.timezone(datetime.timedelta(hours=8))


class KasaUtils:
    async def get_power_usage(self, plug_id: PlugID) -> dict:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            plug_url_suffix = f"/{plug_id}" if plug_id != PlugID.POWER_STRIP else ""
            await client.subscribe(f"hs300/emeter{plug_url_suffix}")
            async for message in client.messages:  # we only need the 1st message
                payload = {**json.loads(message.payload), "id": plug_id}
                break

        return payload

    async def get_power_usage_multiple(self, plug_ids: Iterable[PlugID]) -> dict:
        payloads = {}
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            for plug_id in plug_ids:
                plug_url_suffix = f"/{plug_id}" if plug_id != PlugID.POWER_STRIP else ""
                await client.subscribe(f"hs300/emeter{plug_url_suffix}")

            async for message in client.messages:
                payload = json.loads(message.payload)
                topic = str(message.topic)
                id_num = int(
                    PlugID.POWER_STRIP
                    if topic == "hs300/emeter"
                    else (topic.rsplit("/", maxsplit=1)[-1])
                )
                payloads[payload["name"]] = {**payload, "id": id_num}
                if len(payloads) == len(plug_ids):
                    break

        return dict(sorted(payloads.items(), key=lambda x: x[1]["id"]))

    async def turn_on(self, plug_id: PlugID) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(
                f"hs300/command/on/{plug_id}", json.dumps({}).encode(), qos=MQTTQoS.AT_LEAST_ONCE
            )
        return f"Turned on plug: {plug_id!s}"

    async def turn_off(self, plug_id: PlugID) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(
                f"hs300/command/off/{plug_id}", json.dumps({}).encode(), qos=MQTTQoS.AT_LEAST_ONCE
            )
        return f"Turned off plug: {plug_id!s}"

    async def toggle(self, plug_id: PlugID, status: str | None = None) -> str:
        async with Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.publish(
                f"hs300/command/toggle/{plug_id}",
                json.dumps({"status": status}).encode(),
                qos=MQTTQoS.AT_LEAST_ONCE,
            )

        return f"Toggled plug: {plug_id!s}"

    async def get_daily_power_usage(self, plug_id: PlugID) -> float:
        async with AsyncSession(engine) as session:
            table = plug_mapping.get(plug_id, HS300)

            # get all data from the plug within 24HR
            query = select(table).where(
                table.create_time >= datetime.datetime.now(TZ) - datetime.timedelta(days=1)
            )
            # log the query as sql statement
            result = (await session.exec(query)).all()
            if not result:  # return -1 if no record found
                return -1.0

            # calculate the total power usage within 24HR(5s interval) and convert to kWh
            return sum(item.power for item in result) / 1000 * 5 / 3600


class KasaResponseFormatter(BaseClassMixin):
    @classmethod
    async def format_power_usage(cls, payload: dict) -> discord.Embed:
        return await cls.create_embed(
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

    @classmethod
    async def format_daily_usage(cls, data: Emeter) -> discord.Embed:
        return await cls.create_embed(
            "Daily Power Usage Report",
            f"Today you used {data.W} Wh of electricity",
            Field(name="Total Energy(kWh)", value=data.total_wh),
            Field(name="Voltage(V)", value=data.voltage),
            Field(name="Current(A)", value=data.current),
            Field(name="Power(W)", value=data.power),
            color=(discord.Color.green() if data.status else discord.Color.from_rgb(0, 0, 0)),
        )
