import os
import sys

# Set up nice logging
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

def get_clean_timestamp():
    # Format: Year-Month-Day_Hour-Minute-Second
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def setup_logging():
    # Configuring the root logger instead of 'uvicorn' to capture logs from all libraries
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Define the log file name with a timestamp
    log_filename = f"logs/snappy_v2_{get_clean_timestamp()}.log"

    # Stream handler (to console)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)  # Set this as needed

    # File handler (to file, with rotation)
    f_handler = RotatingFileHandler(log_filename, maxBytes=10485760, backupCount=5)
    f_handler.setLevel(logging.INFO)  # Set this as needed

    # Common log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

setup_logging()


# The following three lines of code allow for dropping an 'embed()'
# into a page rendering method and returning an interactive
# shell when the embed is hit. Exit with ctl-D
from IPython import embed
import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands

# Define the intents
intents = discord.Intents.default()  # Defaults enable only the message content intent
intents.messages = True
intents.message_content = True  # Make sure this is enabled
intents.members = True  # Enable the member intent to access member data if needed

# Initialize the bot with a command prefix and the defined intents
bot = commands.Bot(command_prefix='!', intents=intents)

# In-memory data structure to store events
events = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def create_event(ctx, event_id: str, *, description: str):
    """Create a new camping event with a unique ID and description."""
    if event_id in events:
        await ctx.send(f"Event ID `{event_id}` already exists.")
    else:
        events[event_id] = {'description': description, 'attendees': []}
        await ctx.send(f"Event `{event_id}` created successfully!")

@bot.command()
async def list_events(ctx):
    """List all camping events."""
    if events:
        for event_id, info in events.items():
            
            await ctx.send(f"**{event_id}**: {info['description']} Attendees: {len(info['attendees'])} .. {info['attendees']}")
    else:
        await ctx.send("No events have been created yet.")
@bot.command()
async def attend(ctx, event_id: str):
    """Request to attend a camping event by its ID."""
    if event_id in events:
        if ctx.author not in events[event_id]['attendees']:
            events[event_id]['attendees'].append(ctx.author)
            await ctx.send(f"You have been added to the attendees list for event `{event_id}`.")
        else:
            await ctx.send("You are already on the attendees list for this event.")
    else:
        await ctx.send(f"No event found with ID `{event_id}`.")

# Replace 'your_bot_token' with your actual Discord bot token
bot.run(sys.argv[1])  # This should be your bot's token
