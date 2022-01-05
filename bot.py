# bot.py
import aiocron
import csv
import datetime
import os
import re
import json
import yaml

import discord
from dotenv import load_dotenv
import sheetake
import logging

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Logging configuration
logging.basicConfig(level=logging.INFO)

client = discord.Client()

advent_calendar = dict()
trivia = dict()
training_links = dict()

creds = sheetake.auth()

sport_sheets = [sheetake.Worksheet(creds, '1HZh6kkX4YWx_S4KwmgLosf4vhfhbuIi0jZpzEhZwXr0', 'Arkusz1'), sheetake.Worksheet(creds, '1QsJjcYdibVYhk7OJB2nBNRYat6U5TaTB_TQ_xaClSuM', 'Sheet1')]
for sport_sheet in sport_sheets:
    sport_sheet.update_values()

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
verification_channel_ids = []
verification_role_id = {}

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
    for sport_sheet in sport_sheets:
        try:
            today_link = sport_sheet.get_training_links()[today][0]
            if (len(today_link.strip()) > 0):
                training_link = f"Dzisiejszy trening ({today}) :mechanical_arm: : {today_link}"
                for channel_id in sport_ids:
                    await client.get_channel(channel_id).send(training_link)
        except KeyError:
            pass



def compare_emojis(reaction_emoji):
    return reaction_emoji.name == "✅"

def read_roles(reaction):
    try:
        config = open('role_config.yaml',)
    except FileNotFoundError:
        return None
    message_id = reaction.message_id
    emoji_name = reaction.emoji.name
    roles = yaml.load(config, Loader=yaml.FullLoader)
    role_info_message = int(roles['role_info_message_id'])
    roles_kv = roles['roles']
    if message_id == role_info_message and emoji_name in roles_kv:
        return int(roles_kv[emoji_name])
    return None

async def add_role(member, role_id):
    role_to_add = discord.utils.get(member.guild.roles, id=role_id)
    await member.add_roles(role_to_add)

# We need to have a workaround for getting reaction user, as when reaction is removed, member is None
async def remove_role(reaction, role_id):
    guild = client.get_guild(reaction.guild_id)
    member = await guild.fetch_member(reaction.user_id)
    role_to_remove = discord.utils.get(guild.roles, id=role_id)
    await member.remove_roles(role_to_remove)

def ensure_user_exists(sheet, user):
    if not user in sheet.get_users():
        print(f"{user} is not not on the list (length: {len(sheet.get_users())}, contents: {sheet.get_users()}")
        sheet.write_cell(len(sheet.get_users())+2, 2, user)
        sheet.update_values()

async def parse_fitness_reaction(message, user_id):
    matcher = re.findall(r'\d{2}-\d{2}-\d{4}', str(message.content))
    if matcher:
        user = await client.fetch_user(user_id)
        for sport_sheet in sport_sheets:
            sport_sheet.update_values()
            try:
                ensure_user_exists(sport_sheet, str(user))
                col = sport_sheet.get_users().index(str(user)) + 2
                row = sport_sheet.get_training_links()[matcher[0]][1] + 3 # Offsets needed for correct pos
                sport_sheet.mark_done(col, row, state)
            except:
                pass

async def handle_reaction(reaction, state):
    role_id = read_roles(reaction)
    if role_id:
        await add_role(reaction.member, role_id)
    if compare_emojis(reaction.emoji):
        print("Looks like somebody finished something!")
        user_id = reaction.user_id
        channel = await client.fetch_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)
        if 'sport' in msg.channel.name:
            await parse_fitness_reaction(msg, user_id)
    if reaction.emoji.name == "🔖" and state == "done":
        user_id = reaction.user_id
        channel = await client.fetch_channel(reaction.channel_id)
        msg = await channel.fetch_message(reaction.message_id)
        handle_bookmark(msg, user_id)

def handle_bookmark(message, user_id):
    print(f"This ({message.content}) has been bookmarked by {user_id}!")

@client.event
async def on_raw_reaction_add(reaction):
    await handle_reaction(reaction, "done")

@client.event
async def on_raw_reaction_remove(reaction):
    await handle_reaction(reaction, "")

@client.event
async def on_message(message):
    if message.channel.id in verification_channel_ids and message.content.strip().lower() == 't':
        print(f'{message.author} verified!')
        await add_role(message.author, verification_role_id[message.guild.id])

async def parse_sport_history(channel):
    async for message in channel.history(limit=200):
        for reaction in message.reactions:
            if reaction.emoji == "✅":
                async for user in reaction.users():
                    await parse_fitness_reaction(message, user.id, dry_run=True)

async def parse_bookmark_reactions(channel):
    async for message in channel.history(limit=2000):
        for reaction in message.reactions:
            if reaction.emoji == "🔖":
                async for user in reaction.users():
                    handle_bookmark(message, user.id)

@client.event
async def on_ready():
    global channel_ids
    for guild in client.guilds:
        #try:
        #    print(await client.http.request(discord.http.Route('GET', '/guilds/{guild_id}/scheduled-events', guild_id=guild.id)))
        #    event = {
        #        'name': 'Orpheus presents',
        #        'description': 'This is a test event created by Orpheus the Bot',
        #        'scheduled_start_time': '2021-12-23T17:00:00.060000+00:00',
        #        'scheduled_end_time': '2021-12-23T19:00:00.060000+00:00',
        #        'privacy_level': 2,
        #        'entity_metadata': {'location': 'Metaverse'},
        #        'entity_type': 3,
        #    }
        #    print(await client.http.request(discord.http.Route('POST', '/guilds/{guild_id}/scheduled-events', guild_id=guild.id), json=event))
        #except:
        #    pass
        logging.info(f'{client.user} has connected to Discord server {guild}!')
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if 'music' in channel.name:
                    channel_ids.append(channel.id)
                if 'sport' in channel.name:
                    sport_ids.append(channel.id)
                    await parse_sport_history(channel)
                if 'ciekawostka-dnia' in channel.name:
                    trivia_channel_ids.append(channel.id)
                if 'wydarzenia' in channel.name and 'wydarzenia-' not in channel.name:
                    events_channel_ids.append(channel.id)
                if 'weryfikacja' in channel.name:
                    verification_channel_ids.append(channel.id)
                try:
                    await parse_bookmark_reactions(channel)
                except discord.errors.Forbidden:
                    pass
        for thread in guild.threads:
            print(f"Found a thread: {thread}")
            if thread.parent_id in sport_ids:
                print(f"This thread ({thread}) is part of the sports channel with parent ID {thread.parent_id}, I'm in!")
                await thread.join()
        for role in guild.roles:
            if role.name == "weryfikacja":
                print(f"Verification role for {guild.name} ({guild.id}) is {role.id}")
                verification_role_id[guild.id] = role.id


client.run(TOKEN)