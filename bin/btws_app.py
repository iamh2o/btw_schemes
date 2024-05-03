import os
import sys

# Set up logging
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

def get_clean_timestamp():
    # Format: Year-Month-Day_Hour-Minute-Second
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_filename = f"logs/btw_schemes_{get_clean_timestamp()}.log"
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    f_handler = RotatingFileHandler(log_filename, maxBytes=10485760, backupCount=5)
    f_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

setup_logging()

from IPython import embed
import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
events = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def create_event(ctx, event_id: str, *, description: str):
    if event_id in events:
        await ctx.send(f"Event ID `{event_id}` already exists.")
    else:
        events[event_id] = {'description': description, 'requests': []}
        await ctx.send(f"Event `{event_id}` created successfully!")

@bot.command(name="list_invite_reqs")
async def list_invite_reqs(ctx):
    if events:
        for event_id, info in events.items():
            response = f"**{event_id}** - {info['description']}\n"
            for request in info['requests']:
                response += f"    - {request['user'].name}: Email {request['email']}, Cell {request['cell']}, Color {request['color']}, Status: {request['status']}\n"
            await ctx.send(response)
    else:
        await ctx.send("No events have been created yet.")

@bot.command(name="request_invitation")
async def request_invitation(ctx, event_id: str):
    if event_id not in events:
        await ctx.send(f"No event found with ID `{event_id}`.")
        return

    # Ask for additional info
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        await ctx.send("Please enter your contact email:")
        email_msg = await bot.wait_for('message', timeout=60.0, check=check)
        email = email_msg.content

        await ctx.send("Please enter your contact cell number:")
        cell_msg = await bot.wait_for('message', timeout=60.0, check=check)
        cell = cell_msg.content

        await ctx.send("Please enter your favorite color:")
        color_msg = await bot.wait_for('message', timeout=60.0, check=check)
        color = color_msg.content

    except asyncio.TimeoutError:
        await ctx.send("You did not respond in time!")
        return

    # Save the request
    request = {
        'user': ctx.author,
        'email': email,
        'cell': cell,
        'color': color,
        'status': 'Pending'
    }
    events[event_id]['requests'].append(request)
    await ctx.send(f"Your invitation request has been submitted for event `{event_id}`.")


@bot.command(name="alter_invitation_status")
async def alter_invitation_status(ctx, event_id: str, user_id: int, new_status: str):
    if event_id not in events:
        await ctx.send(f"No event found with ID `{event_id}`.")
        return
    if new_status not in ['Pending', 'Invited', 'Attending', 'Waitlist', 'Revoked']:
        await ctx.send("Invalid status. Valid statuses are: Pending, Invited, Attending, Waitlist, Revoked.")
        return

    for request in events[event_id]['requests']:
        if request['user'].id == user_id:
            old_status = request['status']
            request['status'] = new_status
            user = request['user']
            try:
                await user.send(f"Your invitation status for the event `{event_id}` - `{events[event_id]['description']}` has been changed from `{old_status}` to `{new_status}`.")
                await ctx.send(f"Updated status for {user.name} to `{new_status}`.")
            except discord.errors.Forbidden:
                await ctx.send("Error: Unable to send DM to the user. They might have DMs disabled.")
            return

    await ctx.send(f"No request found for user with ID `{user_id}` in event `{event_id}`.")


@bot.command(name="list_events")
async def list_events(ctx):
    if events:
        for event_id, info in events.items():
            status_count = {status: 0 for status in ['Pending', 'Invited', 'Attending', 'Waitlist', 'Revoked']}
            for request in info['requests']:
                if request['status'] in status_count:
                    status_count[request['status']] += 1
            status_details = ', '.join([f"{status}: {count}" for status, count in status_count.items()])
            await ctx.send(f"**{event_id}** - {info['description']} - {status_details}")
    else:
        await ctx.send("No events have been created yet.")
        

@bot.command(name="list_event_invites")
async def list_event_invites(ctx):
    if not events:
        await ctx.send("No events have been created yet.")
        return

    for event_id, info in events.items():
        response = f"**Event ID: {event_id} - {info['description']}**\n"
        if not info['requests']:
            response += "    No invite requests yet.\n"
        else:
            for request in info['requests']:
                response += f"    - Username: {request['user'].name}, UserID: {request['user'].id}, Status: {request['status']}\n"
        await ctx.send(response)


# Replace 'your_bot_token' with your actual Discord bot token
bot.run(sys.argv[1])
