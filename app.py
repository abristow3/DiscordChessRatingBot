import os
import requests
import discord
from dotenv import load_dotenv
import json
from discord.ext import tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
NAME_CHANGE_CHANNEL = 1212819469806739486
ACCOUNT_LINK_CHANNEL = 1213837193643171911
with open('linked_members.json', 'r') as openfile:
    # Reading from json file
    linked_members = dict(json.load(openfile))


@tasks.loop(seconds=60)
async def task_loop():
    print("TASK LOOP")
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    for k, v in linked_members.items():
        member = guild.get_member(k)
        chess_user = v

        for role in member.roles:
            if role.name == 'linked-member':
                user_nick = member.nick.split("|")[0].replace(" ", "")
                break
            elif role.name == 'member':
                user_nick = member.nick
                break

        # Which game mode tag does the user have?
        for role in member.roles:
            if role.name == 'bullet':
                game_mode = 'bullet'
                break
            if role.name == 'blitz':
                game_mode = 'blitz'
                break
            if role.name == 'rapid':
                game_mode = 'rapid'
                break
            if role.name == 'daily':
                game_mode = 'daily'
                break

        url = f"https://api.chess.com/pub/player/{chess_user}/stats"
        headers = {'User-Agent': chess_user}
        r = requests.get(url=url, headers=headers)
        rdata = r.json()
        rating = rdata[f"chess_{game_mode}"]['last']['rating']
        await member.edit(nick=f"{user_nick} | {game_mode.capitalize()}: {rating}")


@client.event
async def on_ready():
    task_loop.start()


@client.event
async def on_member_join(member):
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    roles = await guild.fetch_roles()
    for role in roles:
        if role.name == 'member':
            await member.add_roles(role)
            break

    member.nick = member.name
    await member.edit(nick=str(member.name))

    # TODO Set roles by ID rather than looping over role list everytime

    # TODO logs channel for bot logs for error messages


@client.event
async def on_message(message):
    """
    Automatic Name Changes
    Need to add the logic for linked-members
    """
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    if message.channel.id == NAME_CHANGE_CHANNEL:
        author = message.author

        for role in author.roles:
            if role.name == "linked-member":
                user_rating = author.nick.split("|")[-1]
                await author.edit(nick=f"{message.content} | {user_rating}")
                break
            elif role.name == "member":
                await author.edit(nick=f"{message.content}")
                break

    # Account link message
    if message.channel.id == ACCOUNT_LINK_CHANNEL:
        author = message.author
        for role in author.roles:
            if role.name == 'bullet':
                game_mode = 'bullet'
                break
            if role.name == 'blitz':
                game_mode = 'blitz'
                break
            if role.name == 'rapid':
                game_mode = 'rapid'
                break
            if role.name == 'daily':
                game_mode = 'daily'
                break

        for role in author.roles:
            if role.name == 'linked-member':
                user_nick = author.nick.split("|")[0].replace(" ", "")
                break
            elif role.name == 'member':
                user_nick = author.nick
                break

        chess_user = str(message.content)

        linked_members[author.id] = chess_user
        with open("linked_members.json", "w") as outfile:
            json.dump(linked_members, outfile)

        url = f"https://api.chess.com/pub/player/{chess_user}/stats"
        headers = {'User-Agent': chess_user}
        r = requests.get(url=url, headers=headers)
        rdata = r.json()

        rating = rdata[f"chess_{game_mode}"]['last']['rating']
        await author.edit(nick=f"{user_nick} | {game_mode.capitalize()}: {rating}")

        # Add linked-member role and remove member role
        roles = await guild.fetch_roles()
        for role in roles:
            if role.name == 'linked-member':
                await author.add_roles(role)

            if role.name == 'member':
                await author.remove_roles(role)

        await message.channel.delete_messages([message])


@client.event
async def on_raw_reaction_add(payload):
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    if payload.channel_id != ACCOUNT_LINK_CHANNEL:
        return
    else:
        channel = await client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # iterating through each reaction in the message
        for r in message.reactions:
            users = [user async for user in r.users()]
            # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
            if payload.member in users and not payload.member.bot and str(r) != str(payload.emoji):
                # removes the reaction
                await message.remove_reaction(r.emoji, payload.member)

        roles = await guild.fetch_roles()
        # Which reaction did they use?
        if str(payload.emoji) == '🔫':
            for role in roles:
                if role.name == 'bullet':
                    await payload.member.add_roles(role)

        if str(payload.emoji) == '⚡':
            for role in roles:
                if role.name == 'blitz':
                    await payload.member.add_roles(role)

        if str(payload.emoji) == '⌚':
            for role in roles:
                if role.name == 'rapid':
                    await payload.member.add_roles(role)

        if str(payload.emoji) == '🌞':
            for role in roles:
                if role.name == 'daily':
                    await payload.member.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    if payload.channel_id != ACCOUNT_LINK_CHANNEL:
        return
    else:
        print("IN LOGIC")
        roles = await guild.fetch_roles()
        member = guild.get_member(payload.user_id)
        # Which reaction did they use?
        if str(payload.emoji) == '🔫':
            for role in roles:
                if role.name == 'bullet':
                    await member.remove_roles(role)

        if str(payload.emoji) == '⚡':
            for role in roles:
                if role.name == 'blitz':
                    await member.remove_roles(role)

        if str(payload.emoji) == '⌚':
            for role in roles:
                if role.name == 'rapid':
                    await member.remove_roles(role)

        if str(payload.emoji) == '🌞':
            for role in roles:
                if role.name == 'daily':
                    await member.remove_roles(role)


client.run(TOKEN)
