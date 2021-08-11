# bot.py
import aiocron
import csv
import datetime
import os

import discord
from dotenv import load_dotenv
import sheetake

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

advent_calendar = dict()
trivia = dict()
training_links = dict()

creds = sheetake.auth()

values = sheetake.get_sheet_done(creds)
for row in values[2:]:
    training_links[row[0]] = row[1]
print(training_links)

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
async def cronjob1():
    today = datetime.date.today().strftime('%Y-%m-%d')
    theme = advent_calendar[today]
    for channel_id in channel_ids:
        await client.get_channel(channel_id).send(f"Dzisiejszy temat to: {theme}")


@aiocron.crontab('0 6 * * *')
async def cronjob2():
    today = datetime.date.today().strftime('%Y-%m-%d')
    trivia_of_the_day = trivia[today]
    for channel_id in trivia_channel_ids:
        await client.get_channel(channel_id).send(trivia_of_the_day)


@aiocron.crontab('45 9 * * 2,4')
async def cronjob3():
    for channel_id in events_channel_ids:
        await client.get_channel(channel_id).send("Za kwadrans kawka na kanale głosowym Relaks! ☕")


@aiocron.crontab('0 10 * * 2,4')
async def cronjob4():
    for channel_id in events_channel_ids:
        await client.get_channel(channel_id).send("Zapraszamy na kanał głosowy Relaks na wspólną kawę! ☕")


@aiocron.crontab('* * * * *')
async def cronjob5():
    print("Cronjob5")
    today = datetime.date.today().strftime('%d-%m-%Y')
    today = '16-08-2021'
    training_link = f"Dzisiejszy trening :mechanical_arm: : {training_links[today]}"
    for channel_id in sport_ids:
        await client.get_channel(channel_id).send(training_link)


@client.event
async def on_ready():
    global channel_ids
    for guild in client.guilds:
        print(f'{client.user} has connected to Discord server {guild}!')
        if "DoomHammer's server chapter 2" in str(guild):
            print(f"Diving into {guild}")
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    if 'music' in channel.name:
                        channel_ids.append(channel.id)
                    if 'sport' in channel.name:
                        sport_ids.append(channel.id)
                        print(f"Adding {channel.id} ({channel.name})")
                    if 'ciekawostka-dnia' in channel.name:
                        trivia_channel_ids.append(channel.id)
                    if 'wydarzenia' in channel.name and 'wydarzenia-' not in channel.name:
                        events_channel_ids.append(channel.id)


client.run(TOKEN)
