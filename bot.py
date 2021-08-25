# bot.py
import aiocron
import csv
import datetime
import os
import re
import json

import discord
from dotenv import load_dotenv
#import sheetake
import logging

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Logging configuration
logging.basicConfig(level=logging.INFO)

client = discord.Client()

advent_calendar = dict()
trivia = dict()
training_links = dict()

#creds = sheetake.auth()

#values = sheetake.get_sheet_done(creds)
#users = [x.strip() for x in values[1][2:]]
#for i, row in enumerate(values[2:]):
#    training_links[row[0]] = [row[1], i]

with open('themes.csv') as f:
    csv_reader = csv.reader(f)
    for line in csv_reader:
        advent_calendar[line[0]] = line[1]

files_to_read = ['webaccessibility.csv', 'photography.csv', 'music.csv', 'eme-love.txt', 'tools.csv']
for file_to_read in files_to_read:
    with open(file_to_read) as f:
        csv_reader = csv.reader(f)
        for line in csv_reader:
            trivia[line[0]] = line[1]

channel_ids = []
sport_ids = []
trivia_channel_ids = []
events_channel_ids = []


@aiocron.crontab('15 4 * * *')
async def advent_event():
    today = datetime.date.today().strftime('%Y-%m-%d')
    try:
        theme = advent_calendar[today]
    except KeyError:
        return
    for channel_id in channel_ids:
        await client.get_channel(channel_id).send(f"Dzisiejszy temat to: {theme}")


@aiocron.crontab('0 6 * * *')
async def trivia_event():
    today = datetime.date.today().strftime('%Y-%m-%d')
    try:
        trivia_of_the_day = trivia[today]
    except KeyError:
        return
    for channel_id in trivia_channel_ids:
        await client.get_channel(channel_id).send(trivia_of_the_day)


@aiocron.crontab('45 9 * * 2,4')
async def coffee_reminder():
    for channel_id in events_channel_ids:
        await client.get_channel(channel_id).send("Za kwadrans kawka na kanale głosowym Relaks! ☕")


@aiocron.crontab('0 10 * * 2,4')
async def coffee_invite():
    for channel_id in events_channel_ids:
        await client.get_channel(channel_id).send("Zapraszamy na kanał głosowy Relaks na wspólną kawę! ☕")


@aiocron.crontab('0 5 * * *')
async def fitness_event():
    today = datetime.date.today().strftime('%d-%m-%Y')
    try:
        today_link = training_links[today][0]
    except KeyError:
        return
    training_link = f"Dzisiejszy trening ({today}) :mechanical_arm: : {today_link}"
    for channel_id in sport_ids:
        await client.get_channel(channel_id).send(training_link)


def compare_emojis(reaction_emoji):
    return reaction_emoji.name == "✅"

def read_roles(reaction):
    message_id = reaction.message_id
    emoji_name = reaction.emoji.name
    config = open('role_config.json',)
    roles = json.load(config)
    role_info_message = int(roles['role_info_message_id'])
    roles_kv = roles['roles']
    if message_id == role_info_message and emoji_name in roles_kv:
        return int(roles_kv[emoji_name])
    return None

async def add_role(member, role_id):
    role_to_add = discord.utils.get(member.guild.roles, id=role_id)
    await member.add_roles(role_to_add)

async def remove_role(reaction, role_id):
    guild = client.get_guild(reaction.guild_id)
    member = await guild.fetch_member(reaction.user_id)
    role_to_remove = discord.utils.get(guild.roles, id=role_id)
    await member.remove_roles(role_to_remove)

@client.event
async def on_raw_reaction_add(reaction):
    role_id = read_roles(reaction)
    if role_id:
        await add_role(reaction.member, role_id)
    if compare_emojis(reaction.emoji):
        user_id = reaction.user_id
        channel = await client.fetch_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)
        if 'sport' in msg.channel.name:
            matcher = re.findall(r'\d{2}-\d{2}-\d{4}', str(msg.content))
            if matcher:
                user = await client.fetch_user(user_id)
                try:
                    col = users.index(str(user)) + 2
                except ValueError:
                    return
                row = training_links[matcher[0]][1] + 3 # Offsets needed for correct pos
                sheetake.mark_done(col, row, "done")

@client.event
async def on_raw_reaction_remove(reaction):
    role_id = read_roles(reaction)
    if role_id:
        await remove_role(reaction, role_id)
    if compare_emojis(reaction.emoji):
        user_id = reaction.user_id
        channel = await client.fetch_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)
        if 'sport' in msg.channel.name:
            matcher = re.findall(r'\d{2}-\d{2}-\d{4}', str(msg.content))
            if matcher:
                user = await client.fetch_user(user_id)
                col = users.index(str(user)) + 2
                row = training_links[matcher[0]][1] + 3 # Offsets needed for correct pos
                sheetake.mark_done(col, row, "")

@client.event
async def on_ready():
    global channel_ids
    for guild in client.guilds:
        logging.info(f'{client.user} has connected to Discord server {guild}!')
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if 'music' in channel.name:
                    channel_ids.append(channel.id)
                if 'sport' in channel.name:
                    sport_ids.append(channel.id)
                if 'ciekawostka-dnia' in channel.name:
                    trivia_channel_ids.append(channel.id)
                if 'wydarzenia' in channel.name and 'wydarzenia-' not in channel.name:
                    events_channel_ids.append(channel.id)


client.run(TOKEN)
