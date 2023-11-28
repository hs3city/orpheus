# bot.py
import csv
import datetime
import logging
import os
from typing import Dict, List

import aiocron
import discord
import yaml
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Logging configuration
logging.basicConfig(level=logging.INFO)


# Discord configuration
intents = discord.Intents.all()
client = discord.Client(intents=intents)

advent_calendar = {}

files_to_read = ["themes.csv", "music_advent_2023.csv"]
for file_to_read in files_to_read:
    with open(file_to_read) as f:
        csv_reader = csv.reader(f)
        for line in csv_reader:
            advent_calendar[line[0]] = line[1]

channel_ids: List[int] = []

verification_channel_ids = []
verification_role_id: Dict[int, int] = {}


@aiocron.crontab("45 4 * * *")
async def advent_event():
    today = datetime.date.today().strftime("%Y-%m-%d")
    try:
        theme = advent_calendar[today]
    except KeyError:
        return
    for channel_id in channel_ids:
        await client.get_channel(channel_id).send(f"Dzisiejszy temat to: {theme}")


def read_roles(reaction):
    try:
        config = open(
            "role_config.yaml",
        )
    except FileNotFoundError:
        return None
    message_id = reaction.message_id
    emoji_name = reaction.emoji.name
    roles = yaml.safe_load(config, Loader=yaml.FullLoader)
    role_info_message = int(roles["role_info_message_id"])
    roles_kv = roles["roles"]
    if message_id == role_info_message and emoji_name in roles_kv:
        return int(roles_kv[emoji_name])
    return None


async def add_role(member, role_id):
    role_to_add = discord.utils.get(member.guild.roles, id=role_id)
    await member.add_roles(role_to_add)


async def handle_reaction(reaction, state):
    role_id = read_roles(reaction)
    if role_id:
        await add_role(reaction.member, role_id)


@client.event
async def on_raw_reaction_add(reaction):
    await handle_reaction(reaction, "done")


@client.event
async def on_raw_reaction_remove(reaction):
    await handle_reaction(reaction, "")


@client.event
async def on_message(message):
    if (
        message.channel.id in verification_channel_ids
        and message.content.strip().lower() == "t"
    ):
        logging.info(f"{message.author} verified!")
        await add_role(message.author, verification_role_id[message.guild.id])


@client.event
async def on_ready():
    global channel_ids
    for guild in client.guilds:
        logging.info(f"{client.user} has connected to Discord server {guild}!")
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if "music" in channel.name:
                    channel_ids.append(channel.id)
                if "weryfikacja" in channel.name:
                    verification_channel_ids.append(channel.id)
                    logging.info(
                        f"Verification channel for {guild.name} ({guild.id}) is {channel.id}"
                    )
        for role in guild.roles:
            if role.name == "weryfikacja":
                logging.info(
                    f"Verification role for {guild.name} ({guild.id}) is {role.id}"
                )
                verification_role_id[guild.id] = role.id


client.run(TOKEN)
