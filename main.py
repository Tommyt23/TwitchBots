from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch

import asyncio
import random
import apikeys as dontLeak
import re

APP_ID = dontLeak.clientID
APP_SECRET = dontLeak.clientSecret
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_MANAGE_BROADCAST]
TARGET_CHANNEL = 'trashpanda_2314'

async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(TARGET_CHANNEL)
    print('Bot is ready!!')
    
async def on_message(msg: ChatMessage):
    print(f'{msg.user.display_name} - {msg.text}')

async def help_command(cmd: ChatMessage):
    await cmd.reply('Commands: !lurk, !yabba, !settings, !score, !welcome, !rank, !poll [question] [time] [option1] [option2], !vote [option]')

async def lurk_command(cmd: ChatMessage):
    chance = random.randint(0, 4)

    if chance == 0:
        await cmd.reply('Thanks for stopping by, enjoy the stream :3')
    elif chance == 1:
        await cmd.reply('We appreciate you being here, even in silent mode ;3')
    elif chance == 2:
        await cmd.reply("Enjoy you lurk, and thanks for haning out")
    elif chance == 3:
        await cmd.reply("Rest easy, we'll keep the stream cozy for you" )
    elif chance == 4:
        await cmd.reply("Take your time, we'll be here when you get back o7")

async def yabba_command(cmd: ChatMessage):
    chance = random.randint(0, 1)

    if chance == 0:
        await cmd.reply('Yabba Yabba Yabba!')
    elif chance == 1:
        await cmd.reply('https://youtu.be/wbHqYDBRdfE')

async def settings_command(cmd: ChatMessage):
    await cmd.reply("Why are you trying to copy my settings when im worse than you?")

async def score_command(cmd: ChatMessage):
    with open('scores.txt', 'r') as file:
        scores = file.read()
        
    await cmd.reply(f"{scores}")

async def welcome_command(cmd: ChatMessage):
    await cmd.reply(f"Welcome {cmd.user.display_name} to the stream!")

async def rank_command(cmd: ChatMessage):
    with open('rank.txt', 'r') as file:
        rank = file.read()
    
    await cmd.reply(f"{rank}")

polls = {}  # store polls

async def poll_command(cmd: ChatMessage):
    message = cmd.text
    match = re.match(r'!poll\s+"([^"]*)"\s+(\d+)\s+(.*)', message)

    if not match:
        await cmd.reply("Usage: !poll \"<question>\" <time(s)> \"<option1>\" \"<option2>\" ...")
        return

    question = match.group(1)
    try:
        time = int(match.group(2))
        if time <= 0:
            await cmd.reply("Poll time must be a positive integer.")
            return
    except ValueError:
        await cmd.reply("Invalid poll time. Please enter a number of seconds.")
        return

    options_str = match.group(3)
    options = re.findall(r'"([^"]*)"', options_str)

    if len(options) < 2:
        await cmd.reply("Please provide at least two options surrounded by quotes.")
        return

    poll_id = cmd.id
    polls[poll_id] = {"question": question, "options": options, "votes": {option: 0 for option in options}}

    await cmd.reply(f"Poll started! Question: {question} Options: {', '.join(options)}. Use !vote [option].")
    await asyncio.sleep(time)

    results = polls.pop(poll_id, None)
    if results:
        vote_results = ", ".join([f"{option}: {count}" for option, count in results["votes"].items()])
        await cmd.reply(f"Poll results: Question: {results['question']} {vote_results}")


async def vote_command(cmd: ChatMessage):
    message = cmd.text
    option = message.split("!vote", 1)[1].strip()  # Get everything after "!vote" and remove leading/trailing spaces.

    if not option:
        await cmd.reply("Usage: !vote [option]")
        return

    voted = False
    for poll in polls.values():
        if option in poll["options"]:
            poll["votes"][option] += 1
            await cmd.reply(f"{cmd.user.display_name} voted for {option}.")
            voted = True
            break #stop after finding a match.
    if not voted:
        await cmd.reply("No active poll with that option.")

#async def sfx_command(cmd: ChatMessage):
    
async def tracker_command(cmd: ChatMessage):
    await cmd.reply("https://tracker.gg/valorant/profile/riot/TrashPanda%23TT23")

async def run_bot():
    bot = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(bot, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await bot.set_user_authentication(token, USER_SCOPE, refresh_token)
    
    chat = await Chat(bot)
    
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)

    chat.register_command('help', help_command)
    chat.register_command('lurk', lurk_command)
    chat.register_command('yabba', yabba_command)
    chat.register_command('settings', settings_command)
    chat.register_command('score', score_command)
    chat.register_command('welcome', welcome_command)
    chat.register_command('poll', poll_command)
    chat.register_command('vote', vote_command)
    chat.register_command('rank', rank_command)
    
    chat.start()
    
    try:
        input('Press Enter TO Stop Bot \n')
    finally:
        chat.stop()
        await bot.close()
        
bot_loop = asyncio.new_event_loop()
asyncio.set_event_loop(bot_loop)

bot_loop.run_until_complete(run_bot())
bot_loop.close()