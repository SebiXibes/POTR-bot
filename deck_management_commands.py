# deck_management_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import uuid
import logging
from deck_manager import DeckManager
from utils import sanitize_input, admin_only, admin_or_gamemaster_only

class DeckManagementCommands(commands.Cog):
    """
    Contains commands related to deck management.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='createdeck', description='Create a new deck.')
    @admin_only
    @app_commands.describe(deck_name='Name of the new deck')
    async def create_deck(self, interaction: discord.Interaction, deck_name: str):
        """
        Command to create a new deck. Admins can choose the deck type via a dropdown menu.
        """
        class DeckTypeSelect(discord.ui.Select):
            predefined_types = ['event_deck', 'dragon_deck', 'sea_deck', 'end_deck']

            def __init__(self):
                options = [
                    discord.SelectOption(label='Event Deck', value='event_deck'),
                    discord.SelectOption(label='Dragon Deck', value='dragon_deck'),
                    discord.SelectOption(label='Sea Deck', value='sea_deck'),
                    discord.SelectOption(label='End Deck', value='end_deck'),
                ]
                super().__init__(placeholder='Select the type of deck to create...', min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                deck_type = self.values[0]
                await interaction.response.defer(ephemeral=True)

                success, response = self.view.bot.deck_manager.create_deck(deck_name, deck_type)
                if success:
                    await interaction.followup.send(f"Deck '{deck_name}' of type '{deck_type}' created successfully.", ephemeral=True)
                    logging.info(f"{interaction.user} created deck '{deck_name}' of type '{deck_type}'.")
                else:
                    await interaction.followup.send(f"Failed to create deck '{deck_name}': {response}", ephemeral=True)

        class DeckTypeView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=60)
                self.add_item(DeckTypeSelect())
                self.bot = bot

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                if hasattr(self, 'message'):
                    await self.message.edit(view=self)

        view = DeckTypeView(self.bot)
        await interaction.response.send_message("Select the type of deck you want to create:", view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @app_commands.command(name='addcardtodeck', description='Add a card to a specific deck.')
    @admin_only
    @app_commands.describe(deck_name='Name of the deck', card_name='Name of the card')
    async def add_card_to_deck(self, interaction: discord.Interaction, deck_name: str, card_name: str):
        """
        Command to add a new card to a deck. Admins must upload an image for the card.
        """
        deck_name = sanitize_input(deck_name)  # Keep sanitization for deck_name
        card_name_original = card_name.strip()  # Preserve original casing and spaces
        await interaction.response.send_message(
            "Please upload the image file for the card as an attachment in your next message.",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.attachments

        try:
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
            if not message.attachments:
                await interaction.followup.send("No attachment detected. Please try the command again.", ephemeral=True)
                return
            if len(message.attachments) > 1:
                await interaction.followup.send("Multiple attachments detected. Please upload only one image file.", ephemeral=True)
                return
            attachment = message.attachments[0]
            if not attachment.content_type.startswith('image/'):
                await interaction.followup.send("The attachment is not an image. Please try the command again.", ephemeral=True)
                return
            os.makedirs('Cards', exist_ok=True)
            name, extension = os.path.splitext(attachment.filename)
            unique_filename = f"{uuid.uuid4()}_{sanitize_input(name)}{extension}"
            image_path = os.path.join('Cards', unique_filename)
            await attachment.save(image_path)
            new_card = {'name': card_name_original, 'image': image_path}
            success, message = self.bot.deck_manager.add_card_to_deck(deck_name, new_card)
            if success:
                await interaction.followup.send(f"Card '{card_name_original}' added to deck '{self.bot.deck_manager.get_original_deck_name(deck_name)}'.", ephemeral=True)
                logging.info(f"{interaction.user} added card '{card_name_original}' to deck '{deck_name}'.")
            else:
                await interaction.followup.send(f"Failed to add card to deck '{deck_name}': {message}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to upload the image. Please try the command again.", ephemeral=True)

    @app_commands.command(name='listdecks', description='List all available decks.')
    async def list_decks(self, interaction: discord.Interaction):
        """
        Command to list all decks currently available in the bot.
        """
        deck_keys = list(self.bot.deck_manager.decks.keys())
        if deck_keys:
            deck_types = {}
            for deck_key in deck_keys:
                deck_info = self.bot.deck_manager.decks[deck_key]
                deck_type = deck_info['type']
                original_name = deck_info.get('original_name', deck_key)
                deck_types.setdefault(deck_type, []).append(original_name)
            embed = discord.Embed(title="Available Decks", color=discord.Color.blue())
            for deck_type, names in deck_types.items():
                formatted_names = '\n'.join(f"- {name}" for name in names)
                embed.add_field(name=deck_type.replace('_', ' ').title(), value=formatted_names, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("No decks are available.", ephemeral=True)

    @app_commands.command(name='listcards', description='List all cards in a deck.')
    @app_commands.describe(deck_name='The name of the deck to list cards from.', display_format='Display format: names or images.')
    async def list_cards_in_deck(self, interaction: discord.Interaction, deck_name: str, display_format: str = "names"):
        """Lists all cards in the specified deck."""
        deck_key = self.bot.deck_manager.get_deck_key(deck_name)
        if not deck_key:
            await interaction.response.send_message(f"Deck '{deck_name}' does not exist.", ephemeral=True)
            return

        deck = self.bot.deck_manager.decks.get(deck_key)

        if display_format.lower() not in ["names", "images"]:
            await interaction.response.send_message("Invalid display format. Please choose 'names' or 'images'.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if display_format.lower() == "names":
            # List card names
            card_names = [card['name'] for card in deck['cards']]
            card_list = '\n'.join(card_names)
            await interaction.followup.send(f"**Cards in Deck '{deck['original_name']}':**\n{card_list}", ephemeral=True)
        elif display_format.lower() == "images":
            # Send card images
            files = []
            for card in deck['cards']:
                image_path = card['image']
                if os.path.exists(image_path):
                    file_extension = os.path.splitext(image_path)[1]
                    file_name = f"{card['name']}{file_extension}"
                    file = discord.File(image_path, filename=file_name)
                    files.append(file)
                else:
                    logging.warning(f"Image not found for card '{card['name']}' in deck '{deck['original_name']}'")

            if files:
                MAX_FILES_PER_MESSAGE = 10
                for i in range(0, len(files), MAX_FILES_PER_MESSAGE):
                    files_batch = files[i:i + MAX_FILES_PER_MESSAGE]
                    await interaction.followup.send(files=files_batch, ephemeral=True)
            else:
                await interaction.followup.send(f"No images found for the cards in deck '{deck['original_name']}'.", ephemeral=True)

    @list_cards_in_deck.autocomplete('display_format')
    async def display_format_autocomplete(self, interaction: discord.Interaction, current: str):
        formats = ["names", "images"]
        return [app_commands.Choice(name=fmt, value=fmt) for fmt in formats if fmt.startswith(current.lower())]
    @list_cards_in_deck.autocomplete('deck_name')
    async def deck_name_autocomplete(self, interaction: discord.Interaction, current: str):
        decks = self.bot.deck_manager.decks
        current_lower = current.lower().replace(" ", "")
        suggestions = []
        for deck_key, deck in decks.items():
            deck_name = deck['original_name']
            deck_name_normalized = deck_name.lower().replace(" ", "")
            if current_lower in deck_name_normalized:
                suggestions.append(app_commands.Choice(name=deck_name, value=deck_name))
        return suggestions[:25]  # Limit to 25 suggestions            
    
    @app_commands.command(name='deletedeck', description='Delete a custom deck.')
    @admin_only
    @app_commands.describe(deck_name='Name of the deck to delete')
    async def delete_deck(self, interaction: discord.Interaction, deck_name: str):
        """
        Command to delete a custom deck. Predefined decks cannot be deleted.
        """
        deck_name = sanitize_input(deck_name)
        deck_exists = deck_name in self.bot.deck_manager.decks
        if not deck_exists:
            await interaction.response.send_message(f"Deck '{deck_name}' does not exist.", ephemeral=True)
            return

        # Confirmation view
        class ConfirmDeleteView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=30)
                self.bot = bot

            @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                success, response = self.bot.deck_manager.delete_deck(deck_name)
                if success:
                    await interaction_button.response.send_message(f"Deck '{deck_name}' deleted successfully.", ephemeral=True)
                    logging.info(f"{interaction_button.user} deleted deck '{deck_name}'.")
                else:
                    await interaction_button.response.send_message(f"Failed to delete deck '{deck_name}': {response}", ephemeral=True)
                self.stop()

            @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                await interaction_button.response.send_message("Deck deletion canceled.", ephemeral=True)
                self.stop()

            async def on_timeout(self):
                if not self.children[0].disabled:
                    await interaction.followup.send("Deck deletion timed out. Please try again.", ephemeral=True)

        view = ConfirmDeleteView(self.bot)
        await interaction.response.send_message(f"Are you sure you want to delete the deck '{deck_name}'?", view=view, ephemeral=True)
    
    @app_commands.command(name='removecard', description='Remove a card from a specific deck.')
    @admin_only
    @app_commands.describe(deck_name='Name of the deck', card_name='Name of the card to remove')
    async def remove_card_from_deck(self, interaction: discord.Interaction, deck_name: str, card_name: str):
        """
        Command to remove a card from a deck.
        """
        deck_key = self.bot.deck_manager.get_deck_key(deck_name)
        if not deck_key:
            await interaction.response.send_message(f"Deck '{deck_name}' does not exist.", ephemeral=True)
            return

        card_name_original = card_name.strip()
        success, message, image_path = self.bot.deck_manager.remove_card_from_deck(deck_key, card_name_original)
        if success:
            # Optionally, delete the image file
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                logging.info(f"Image file '{image_path}' deleted.")
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)