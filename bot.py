# bot.py
import aiocron
import csv
import datetime
import os
import re
import requests
import json

import discord
from dotenv import load_dotenv
import logging
from calendar_parser import Calendar

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USING_GOOGLE = os.getenv('USING_GOOGLE', "True")

# I know this is bad, but i can't properly cast env var to bool
if USING_GOOGLE == "True":
    import sheetake
    creds = sheetake.auth()

    values = sheetake.get_sheet_done(creds)
    users = [x.strip() for x in values[1][2:]]
    for i, row in enumerate(values[2:]):
        training_links[row[0]] = [row[1], i]


# Logging configuration
logging.basicConfig(level=logging.INFO)

client = discord.Client()

advent_calendar = dict()
trivia = dict()
training_links = dict()


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

# Proper @aiocron.crontab('*/15 * * * *')
# @aiocron.crontab('* * * * *')
def calendar_fetcher():
    calendar = Calendar(
            start=datetime.date.today().strftime('%Y-%m-%d'),
            end=(datetime.date.today()+datetime.timedelta(days=6)).strftime('%Y-%m-%d')
        )
    print(calendar.daily_events)

def compare_emojis(reaction_emoji):
    return reaction_emoji.name == "✅"

@client.event
async def on_raw_reaction_add(reaction):
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
    calendar_fetcher()
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
