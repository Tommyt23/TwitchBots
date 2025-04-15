from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch

import asyncio
import apikeys as dontLeak

APP_ID = dontLeak.clientID
APP_SECRET = dontLeak.clientSecret
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_MANAGE_BROADCAST]
TARGET_CHANNEL = 'trashpanda_2314'
BOT_NICK = 'PandaBot' 

twitch: Twitch = None
chat: Chat = None
msgs = set()  # Initialize msgs as an empty set
TIMEOUT_DURATION = 3600  # Timeout duration in seconds (1 hour)

# Set up the bot with the necessary credentials and scopes
async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(TARGET_CHANNEL)
    print('Bot is ready!!')

#store all msgs in a set
msgs = set()

# print messages to console
async def on_message(msg: ChatMessage):
    print(f'{msg.user.display_name} - {msg.text}')
    await check_unique(msg)

#check if msg is unique
async def check_unique(msg: ChatMessage):
    if msg.text not in msgs:
        msgs.add(msg.text)
    else:
        await ban(msg)


async def ban(msg: ChatMessage):
    global chat
    print(f"Timing out {msg.user.display_name} for not having a unique message!")
    await chat.send_message(TARGET_CHANNEL, f'/timeout {msg.user.display_name} {TIMEOUT_DURATION}')
    await chat.send_message(TARGET_CHANNEL, f'{msg.user.display_name} has been timed out for 1 hour for not having a unique message!')

async def run_bot():
    bot = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(bot, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await bot.set_user_authentication(token, USER_SCOPE, refresh_token)
    
    chat = await Chat(bot)
    
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    
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