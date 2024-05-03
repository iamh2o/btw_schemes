import os
import sys

GUILD_ID = 1187265836856115221 ## Server ID, put on comand line

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
schemes = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.command(name="list_invite_reqs")
async def list_invite_reqs(ctx):
    if schemes:
        for scheme_id, info in schemes.items():
            response = f"**{scheme_id}** - {info['description']}\n"
            for request in info['invites']:
                response += f"    - {request['user'].name}: Email {request['email']}, Cell {request['cell']}, Color {request['color']}, Status: {request['status']}\n"
            await ctx.send(response)
    else:
        await ctx.send("No schemes have been created yet.")


# Command to create a scheme
@bot.command()
async def create_scheme(ctx, name, *, description):
    if name in schemes:
        await ctx.send("A scheme with that name already exists.")
        return
    schemes[name] = {'description': description, 'status': 'announced', 'invites': {}}
    await ctx.send(f"Scheme '{name}' created with status 'announced'.")


@bot.command()
async def list_schemes(ctx):
    response = ""
    for name, details in schemes.items():
        status_counts = {status: 0 for status in ['Attending', 'Invited', 'Pending', 'Waitlisted', 'Revoked']}
        for invite in details['invites'].values():
            if invite['status'] in status_counts:
                status_counts[invite['status']] += 1
        response += (f"**Name:** {name}, **Status:** {details['status']}, **Description:** {details['description']}, "
                     f"**Invites:** Attending: {status_counts['Attending']}, Invited: {status_counts['Invited']}, "
                     f"Pending: {status_counts['Pending']}, Waitlisted: {status_counts['Waitlisted']}, Revoked: {status_counts['Revoked']}\n")
    if not response:
        response = "No schemes have been created yet."
    await ctx.send(response)    

# Command to change a scheme's status
@bot.command()
@commands.has_role("scheme-organizer")
async def alter_scheme_status(ctx, name, status):
    if name not in schemes:
        await ctx.send("Scheme not found.")
        return
    if status not in ['announced', 'happening', 'past']:
        await ctx.send("Invalid status. Valid statuses are 'announced', 'happening', or 'past'.")
        return
    schemes[name]['status'] = status
    await ctx.send(f"Scheme '{name}' status updated to {status}.")

# Command to request an invitation to a scheme
@bot.command()
async def request_scheme_invitation(ctx, name):
    
    if name not in schemes:
        await ctx.send("Scheme not found.")
        return
    member = ctx.author
    if member.id in schemes[name]['invites']:
        await ctx.send("You have already requested an invite.")
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

    current_time = datetime.now()

    # Save the request
    request = {
        'user': ctx.author,
        'email': email,
        'cell': cell,
        'color': color,
        'status': 'Pending',
        'submit_date': current_time,
        'last_modified': current_time
    }
    schemes[name]['invites'][member.id] = request

    await ctx.send(f"Your invitation request has been submitted for scheme `{name}`  and is pending..")
    
@bot.command()
async def my_schemes(ctx):
    member = ctx.author
    response = ""
    for name, details in schemes.items():
        if member.id in details['invites']:
            invite = details['invites'][member.id]
            submit_date = invite['submit_date'].strftime("%Y-%m-%d %H:%M:%S")
            last_modified = invite['last_modified'].strftime("%Y-%m-%d %H:%M:%S")
            response += (f"**Scheme Name:** {name}, **Status:** {invite['status']}, "
                         f"**Description:** {details['description']}, "
                         f"**Submit Date:** {submit_date}, **Last Modified:** {last_modified}\n")
    if not response:
        response = "You are not part of any schemes."
    await ctx.send(response)

# Command for admins to list all schemes with detailed status summaries and invite details
@bot.command()
@commands.has_role("scheme-organizer")
async def list_schemes_admin(ctx):
    response = ""
    for name, details in schemes.items():
        response += (f"**Scheme Name:** {name}\n"
                     f"**Status:** {details['status']}\n"
                     f"**Description:** {details['description']}\n"
                     f"**Invitations:**\n")
        if not details['invites']:
            response += "    No invites issued yet.\n"
        else:
            # Detailed invite information
            for user_id, invite in details['invites'].items():
                user = await bot.fetch_user(user_id)  # Fetch user information
                user_details = (f"    - {user.name}#{user.discriminator} (ID: {user_id})\n"
                                f"      Email: {invite.get('email', 'Not provided')}\n"
                                f"      Cell: {invite.get('cell', 'Not provided')}\n"
                                f"      Color: {invite.get('color', 'Not specified')}\n"
                                f"      Status: {invite['status']}\n"
                                f"      Submitted: {invite.get('submit_date', 'Not available')}\n"
                                f"      Last Modified: {invite.get('last_modified', 'Not available')}\n")
                response += user_details

    if not response:
        response = "No schemes have been created yet."
    await ctx.send(response)
    
    
# Command for users to alter their own invitation status
@bot.command()
async def alter_my_scheme_invitation_status(ctx, name, new_status):
    # Try to get the guild from the context, or fetch it using the stored GUILD_ID if in a DM
    guild = ctx.guild or bot.get_guild(GUILD_ID)
    if not guild:
        await ctx.send("This command cannot find the required server.")
        return
    
    channel = discord.utils.get(guild.channels, name='schemebot')
    if not channel:
        await ctx.send("Channel 'schemebot' not found in the server.")
        return
    
       # Now, perform the rest of your command's functionality
    # Example: changing an invite status and notifying the user
    if name not in schemes:
        await ctx.send("Scheme not found.")
        return
    if ctx.author.id not in schemes[name]['invites']:
        await ctx.send("You do not have an invitation to this scheme.")
        return
    
    current_status = schemes[name]['invites'][ctx.author.id]['status']
    
    if new_status == "Revoked":
        schemes[name]['invites'][ctx.author.id]['status'] = 'Revoked'
        schemes[name]['invites'][ctx.author.id]['last_modified'] = datetime.now()
        await ctx.send("Your invitation has been revoked.")
    elif new_status == "Resubmit" and current_status == "Revoked":
        schemes[name]['invites'][ctx.author.id]['status'] = 'Pending'
        schemes[name]['invites'][ctx.author.id]['last_modified'] = datetime.now()
        await ctx.send("Your invitation has been resubmitted and is now pending.")
    else:
        await ctx.send("Invalid request. You can only resubmit a revoked invitation.")
        return
    # Post to a specific channel about the status change
    
    # Log to the specific channel
    await channel.send(f"{ctx.author.display_name}'s invitation status for '{name}' has been updated from {current_status} to {new_status}.")

    # Notify the user directly
    await ctx.send(f"Your invitation status for '{name}' has been updated from {current_status} to {new_status}.")
    
    
# Command to alter the status of a scheme invitation
@bot.command()
@commands.has_role("scheme-organizer")
async def alter_scheme_invitation_status(ctx, name, user_id: int, status):
    if name not in schemes or user_id not in schemes[name]['invites']:
        await ctx.send("Scheme or user not found in the specified scheme.")
        return
    if status not in ['Pending', 'Invited', 'Attending', 'Waitlist', 'Revoked']:
        await ctx.send("Invalid status.")
        return
    schemes[name]['invites'][user_id]['status'] = status
    user = await bot.fetch_user(user_id)
    await user.send(f"Your invitation status for '{name}' has been changed to {status}.")
    await ctx.send(f"Invitation status updated successfully for {user} for {name} to {status}.")

@bot.command()
async def submit_rsvp(ctx, scheme_name):
    member = ctx.author
    if scheme_name not in schemes:
        await ctx.send("Scheme not found.")
        return
    if member.id not in schemes[scheme_name]['invites']:
        await ctx.send("You do not have an invitation to this scheme.")
        return

    invite = schemes[scheme_name]['invites'][member.id]
    if invite['status'] != 'Invited':
        await ctx.send(f"Your invitation is currently in the status '{invite['status']}'. You must be 'Invited' to submit an RSVP.")
        return

    # Collecting RSVP information
    def check(m):
        return m.author == member and m.channel == ctx.channel

    try:
        await ctx.send("Please enter your dietary restrictions:")
        diet = await bot.wait_for('message', timeout=120.0, check=check)
        
        await ctx.send("Please enter any allergies you have:")
        allergies = await bot.wait_for('message', timeout=120.0, check=check)

        await ctx.send("Please enter your date of arrival (YYYY-MM-DD):")
        arrival = await bot.wait_for('message', timeout=120.0, check=check)

        await ctx.send("Please enter your date of departure (YYYY-MM-DD):")
        departure = await bot.wait_for('message', timeout=120.0, check=check)

        current_time = datetime.now()

        # Update the invitation with RSVP details
        invite['diet'] = diet.content
        invite['allergies'] = allergies.content
        invite['arrival'] = arrival.content
        invite['departure'] = departure.content
        invite['status'] = 'Attending'
        invite['last_modified'] = current_time

        await ctx.send("Thank you for submitting your RSVP. Your attendance has been confirmed.")
    except asyncio.TimeoutError:
        await ctx.send("You did not respond in time. Please try to submit your RSVP again.")



# Command to list all available commands
@bot.command()
async def q(ctx):
    commands = [
        "list_schemes :: List all schemes.",
        "create_scheme \"scheme name\" \"scheme channel URL\" :: Create a new scheme.",
        "alter_scheme_status \"scheme name\" \"scheme_status\" :: Change the status of a scheme (announced, happening, past).",
        "request_scheme_invitation \"scheme name\" :: Request an invitation to a scheme. Your request will be pending at first, and when it is altered to one 'Waitlisted', 'Invited', or 'Revoked', you will be notified via direct message with each change.",
        "my_schemes :: List all schemes you have an invitation associated with.",
        "alter_scheme_invitation_status \"scheme name\" \"userid\" \"status\" :: Change the status of a scheme invitation (scheme-organizer role required).",
        "submit_rsvp \"scheme name\" :: Submit an RSVP once you have been invited to a scheme.",
        "alter_my_scheme_invitation_status \"scheme name\" \"new_status\" :: Change your own invitation for a scheme to 'Revoked' (from any status) or 'Resubmit' (from 'Revoked' only).",
        "q :: list all commands."
    ]
    await ctx.send("Available commands:\n" + "\n\n- ".join(commands))



# Replace 'your_bot_token' with your actual Discord bot token
bot.run(sys.argv[1])
