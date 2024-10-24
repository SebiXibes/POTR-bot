# utils.py

# utils.py

import re
import os
import discord
from discord import app_commands
from typing import Tuple, Optional

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable access to message content
intents.members = True  # Enable access to guild members

# Configuration flag to control phase message outputs
SHOW_PHASE_MESSAGES = False  # Set to True to enable phase messages

def sanitize_input(name: str) -> str:
    """
    Sanitizes user input by removing special characters and normalizing whitespace.
    """
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()

def is_admin_check(interaction: discord.Interaction) -> bool:
    """
    Checks if the user is an administrator.
    """
    return interaction.user.guild_permissions.administrator

# Register the admin_only decorator
admin_only = app_commands.check(is_admin_check)

def admin_or_gamemaster_check(interaction: discord.Interaction) -> bool:
    """
    Checks if the user is an administrator or has the 'Game Master' role.
    """
    # Check if user is an administrator
    if interaction.user.guild_permissions.administrator:
        return True
    # Check if user has 'Game Master' role
    gamemaster_role_name = "Game Master"
    guild = interaction.guild
    if guild is None:
        return False
    # Get the 'Game Master' role
    gamemaster_role = discord.utils.get(guild.roles, name=gamemaster_role_name)
    if gamemaster_role is None:
        # If the role does not exist, only admins can proceed
        return False
    # Check if the user has the 'Game Master' role
    if gamemaster_role in interaction.user.roles:
        return True
    return False

# Register the admin_or_gamemaster_only decorator
admin_or_gamemaster_only = app_commands.check(admin_or_gamemaster_check)

# Define deck choices for commands
DECK_CHOICES = [
    app_commands.Choice(name='Event Deck', value='event_deck'),
    app_commands.Choice(name='Dragon Deck', value='dragon_deck'),
    app_commands.Choice(name='Sea Deck', value='sea_deck'),
    app_commands.Choice(name='End Deck', value='end_deck')
]

def create_embed(title: str, card: dict) -> Tuple[discord.Embed, Optional[discord.File]]:
    """
    Creates an embed for the card and attaches the image if available.
    """
    if os.path.exists(card['image']):
        embed = discord.Embed(title=title)
        file = discord.File(card['image'], filename='card.png')
        embed.set_image(url='attachment://card.png')
        return embed, file
    else:
        embed = discord.Embed(title=title)
        embed.add_field(name="Note", value="Image not available.")
        return embed, None
