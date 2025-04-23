from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
import obsws_python as obsws

import asyncio
import random
import apikeys as dontLeak
import re
import time
from collections import deque
import textwrap

APP_ID = dontLeak.clientID
APP_SECRET = dontLeak.clientSecret
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_MANAGE_BROADCAST]
TARGET_CHANNEL = 'trashpanda_2314'
BOT_NICK = 'PandaBot'

try:
    winOBS = obsws.ReqClient(host=dontLeak.serverIP, port=dontLeak.serverPort, password=dontLeak.serverPassword)
    print("Connected to OBS instances")
except:
    print("Failed to connect to OBS instances.")
    quit()


# Set up the bot with the necessary credentials and scopes
async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(TARGET_CHANNEL)
    print('Bot is ready!!')


MAX_CHARS_PER_LINE = 30
MAX_DISPLAYED_LINES = 7

message_queue = deque(maxlen=5)


# print messages to console
async def on_message(msg: ChatMessage):
    print(f'{msg.user.display_name} - {msg.text}')
    message_queue.append(msg)

    while True:
        total_lines = 0
        temp_formatted_messages = []
        for m in message_queue:
            text = m.user.display_name + ": " + m.text
            wrapped_lines = textwrap.wrap(text, width=MAX_CHARS_PER_LINE)
            temp_formatted_messages.extend(wrapped_lines)
            total_lines += len(wrapped_lines)

        if total_lines <= MAX_DISPLAYED_LINES and message_queue:
            formatted_messages = temp_formatted_messages
            break
        elif message_queue:
            message_queue.popleft()  # Remove the oldest message
        else:
            formatted_messages = []
            break

    display_text = "\n".join(formatted_messages)

    try:
        winOBS.set_input_settings(
            'Text',
            {'text': display_text},
            True)
    except Exception as e:
        print(f"Error changing text source: {e}")
        winOBS.trigger_hotkey_by_key_sequence('OBS_KEY_0', pressCtrl=True,
                                              pressShift=False, pressCmd=False, pressAlt=False)
        await asyncio.sleep(10)
        winOBS.trigger_hotkey_by_key_sequence('OBS_KEY_0', pressCtrl=True,
                                              pressShift=False, pressCmd=False, pressAlt=False)


async def on_subscription(sub_event: ChatSub):
    user = sub_event.user_name
    channel = sub_event.channel_name
    sub_type = sub_event.sub_plan_name
    message = sub_event.sub_message.text if sub_event.sub_message else "No message provided."

    if sub_event.is_gift:
        gifter = sub_event.gifter_user_name
        print(f"{user} was gifted a {sub_type} sub by {gifter} in {channel}! Message: {message}")
        await sub_event.chat.send_message(channel,
                                          f"🎉 Huge thanks to {gifter} for gifting a {sub_type} sub to {user}! ❤️")
    else:
        if sub_event.cumulative_months > 1:
            print(
                f"{user} resubscribed to {channel} for {sub_event.cumulative_months} months with a {sub_type} sub! Message: {message}")
            await sub_event.chat.send_message(channel,
                                              f"🥳 Welcome back, {user}! Thanks for the {sub_type} resub for {sub_event.cumulative_months} months! 🙌")
        else:
            print(f"{user} subscribed to {channel} with a {sub_type} sub! Message: {message}")
            await sub_event.chat.send_message(channel, f"Thank you for the sub, {user}! Welcome! 😊")


# Commands:
# !help - List all commands
async def help_command(cmd: ChatMessage):
    await cmd.reply(
        'Commands: !lurk, !yabba, !settings, !score, !welcome, !rank, !tracker, !poll [question] [time] [option1] [option2], !vote [option]')

MINS_BETWEEN_PROMPTS = 7.5

async def send_periodic_help(chat: Chat):
    while True:
        await asyncio.sleep(MINS_BETWEEN_PROMPTS * 60)
        try:
            await chat.send_message(TARGET_CHANNEL,
                                      'For a list of available commands, type !help')
        except Exception as e:
            print(f"Error sending periodic help message: {e}")

# !lurk - Respond with a random lurk message
async def lurk_command(cmd: ChatMessage):
    chance = random.randint(0, 4)

    if chance == 0:
        await cmd.reply('Thanks for stopping by, enjoy the stream :3')
    elif chance == 1:
        await cmd.reply('We appreciate you being here, even in silent mode ;3')
    elif chance == 2:
        await cmd.reply("Enjoy you lurk, and thanks for haning out")
    elif chance == 3:
        await cmd.reply("Rest easy, we'll keep the stream cozy for you")
    elif chance == 4:
        await cmd.reply("Take your time, we'll be here when you get back o7")


# !yabba - Respond with a random Yabba message or a link to a Yabba video
async def yabba_command(cmd: ChatMessage):
    chance = random.randint(0, 1)

    if chance == 0:
        await cmd.reply('Yabba Yabba Yabba!')
    elif chance == 1:
        await cmd.reply('https://youtu.be/wbHqYDBRdfE')


# !settings - Respond with a message about settings
async def settings_command(cmd: ChatMessage):
    await cmd.reply("Why are you trying to copy my settings when im worse than you?")


# !score - Respond with a message about scores (used for custom games)
async def score_command(cmd: ChatMessage):
    with open('scores.txt', 'r') as file:
        scores = file.read()

    await cmd.reply(f"{scores}")


# !welcome - Respond with a welcome message
async def welcome_command(cmd: ChatMessage):
    await cmd.reply(f"Welcome {cmd.user.display_name} to the stream!")


# !rank - Respond with a message about streamer ranks
async def rank_command(cmd: ChatMessage):
    with open('rank.txt', 'r') as file:
        rank = file.read()

    await cmd.reply(f"{rank}")


# !poll - Create a poll with a question, time limit, and options
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


# !vote - Vote for an option in an active poll
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
            break  # stop after finding a match.
    if not voted:
        await cmd.reply("No active poll with that option.")


# async def sfx_command(cmd: ChatMessage):

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
    chat.register_command('tracker', tracker_command)

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