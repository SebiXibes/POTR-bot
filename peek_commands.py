# peek_commands.py

import discord
import random
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, Tuple, Dict
from game_state import GameState
from utils import admin_or_gamemaster_only, create_embed

class PeekCommands(commands.Cog):
    """
    Contains commands related to game mechanics, such as peeking at cards.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name='peek',
        description='Peek at the top card of the Event Deck and send it to a user via DM.'
    )
    @admin_or_gamemaster_only
    @app_commands.describe(
        user="The user to send the peeked card to."
    )
    async def peek_card(self, interaction: discord.Interaction, user: discord.Member):
        """Allows an admin or Game Master to send the top card of the Event Deck to a user via DM."""
        await interaction.response.defer(ephemeral=True)
        game_state = self.bot.game_states.get(interaction.channel_id)
        if not game_state:
            await interaction.followup.send("No game is currently running in this channel.", ephemeral=True)
            return

        deck_key = 'event_deck'  # Automatically use the Event Deck
        await self.handle_peek(interaction, user, game_state, deck_key)

    @app_commands.command(
        name='advancedpeek',
        description='Admin or Game Master sends the top card via DM and let the user decide to move it to the bottom.'
    )
    @admin_or_gamemaster_only
    @app_commands.describe(
        user="The user to send the peeked card to."
    )
    async def advanced_peek(self, interaction: discord.Interaction, user: discord.Member):
        """Admin or Game Master sends the top card via DM and let the user decide to move it to the bottom."""
        await interaction.response.defer(ephemeral=True)
        game_state = self.bot.game_states.get(interaction.channel_id)
        if not game_state:
            await interaction.followup.send("No game is currently running in this channel.", ephemeral=True)
            return

        deck_key = 'event_deck'  # Automatically use the Event Deck
        await self.handle_advanced_peek(interaction, user, game_state, deck_key)

    @app_commands.command(
        name='dragonpeek',
        description='Peek at the top card of the Dragon Deck and send it to a user via DM.'
    )
    @admin_or_gamemaster_only
    @app_commands.describe(
        user="The user to send the peeked card to."
    )
    async def dragon_peek(self, interaction: discord.Interaction, user: discord.Member):
        """Allows an admin or Game Master to send the top card of the Dragon Deck to a user via DM."""
        await interaction.response.defer(ephemeral=True)
        game_state = self.bot.game_states.get(interaction.channel_id)
        if not game_state:
            await interaction.followup.send("No game is currently running in this channel.", ephemeral=True)
            return

        deck_key = 'dragon_deck'  # Use the Dragon Deck
        await self.handle_peek(interaction, user, game_state, deck_key)

    @app_commands.command(
        name='advanceddragonpeek',
        description='Advanced peek on the Dragon Deck with special mechanics.'
    )
    @admin_or_gamemaster_only
    @app_commands.describe(
        user="The user to send the peeked card to."
    )
    async def advanced_dragon_peek(self, interaction: discord.Interaction, user: discord.Member):
        """Admin or Game Master sends the top dragon card via DM and let the user decide to move it to the bottom."""
        await interaction.response.defer(ephemeral=True)
        game_state = self.bot.game_states.get(interaction.channel_id)
        if not game_state:
            await interaction.followup.send("No game is currently running in this channel.", ephemeral=True)
            return

        deck_key = 'dragon_deck'  # Use the Dragon Deck
        await self.handle_advanced_dragon_peek(interaction, user, game_state, deck_key)

    async def handle_peek(self, interaction, user, game_state, deck_key):
        """Handles the peek command for a specified deck."""
        card_tuple = self.peek_top_card(game_state, deck_key)
        if card_tuple:
            card, _ = card_tuple
            try:
                title = f"Top card from {deck_key.replace('_', ' ').title()}"
                embed, file = create_embed(title, card)

                # Send DM to the user
                if file:
                    await user.send(embed=embed, file=file)
                else:
                    await user.send(embed=embed)
                logging.info(f"{interaction.user} sent the top card of the {deck_key} to {user}.")

                # Inform the admin that the peek was successful without revealing card details
                await interaction.followup.send(f"Peeked card has been sent to {user.mention}.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(f"Could not send DM to {user.mention}. They might have DMs disabled.", ephemeral=True)
                logging.warning(f"Failed to send DM to {user}.")
        else:
            await interaction.followup.send(f"No cards left in the {deck_key.replace('_', ' ').title()} to peek at!", ephemeral=True)
            logging.info(f"{interaction.user} tried to peek but the {deck_key} is empty.")

    async def handle_advanced_peek(self, interaction, user, game_state, deck_key):
        """Handles the advanced peek command for a specified deck."""
        card_tuple = self.peek_top_card(game_state, deck_key)
        if card_tuple:
            card, _ = card_tuple
            try:
                # Create the embed and file
                title = f"Top card from {deck_key.replace('_', ' ').title()}"
                embed, file = create_embed(title, card)

                # Handle special cards that cannot be moved
                unmovable_cards = ["black swan", "power overwhelming"]
                if card['name'].lower() in unmovable_cards:
                    embed.add_field(name="Note", value=f"You cannot move '{card['name']}' to the bottom of the deck.")
                    if file:
                        await user.send(embed=embed, file=file)
                    else:
                        await user.send(embed=embed)
                    await interaction.followup.send(f"Peeked card has been sent to {user.mention}.", ephemeral=True)
                    logging.info(f"{interaction.user} sent an unmovable card '{card['name']}' to {user}.")
                else:
                    # Create buttons for interaction
                    view = self.ConfirmView(user, interaction.user, interaction.channel, game_state, deck_key)
                    embed.add_field(name="Question", value="Do you want to move this card to the bottom of the deck?")
                    if file:
                        await user.send(embed=embed, file=file, view=view)
                    else:
                        await user.send(embed=embed, view=view)
                    await interaction.followup.send(f"Options have been sent to {user.mention} via DM.", ephemeral=True)
                    logging.info(f"{interaction.user} sent an advanced peek to {user}.")
            except discord.Forbidden:
                await interaction.followup.send(f"Could not send DM to {user.mention}. They might have DMs disabled.", ephemeral=True)
                logging.warning(f"Failed to send DM to {user}.")
        else:
            await interaction.followup.send(f"No cards left in the {deck_key.replace('_', ' ').title()} to peek at!", ephemeral=True)
            logging.info(f"{interaction.user} tried advanced peek but the {deck_key} is empty.")

    async def handle_advanced_dragon_peek(self, interaction, user, game_state, deck_key):
        """Handles the advanced dragon peek with special mechanics."""
        card_tuple = self.peek_top_card(game_state, deck_key)
        if card_tuple:
            card, _ = card_tuple
            try:
                # Create the embed and file
                title = f"Top card from {deck_key.replace('_', ' ').title()}"
                embed, file = create_embed(title, card)

                if card['name'].lower() != "there be dragons!":
                    # Create buttons for interaction
                    view = self.DragonPeekView(user, interaction.user, interaction.channel, game_state, deck_key, card)
                    embed.add_field(name="Option", value="Do you want to destroy this card and replace it with a copy of 'There be Dragons!'?")
                    if file:
                        await user.send(embed=embed, file=file, view=view)
                    else:
                        await user.send(embed=embed, view=view)
                    await interaction.followup.send(f"Advanced dragon peek options have been sent to {user.mention} via DM.", ephemeral=True)
                    logging.info(f"{interaction.user} performed advanced dragon peek with {user}.")
                else:
                    # If the top card is "There be Dragons!", only send it without option to replace
                    if file:
                        await user.send(embed=embed, file=file)
                    else:
                        await user.send(embed=embed)
                    await interaction.followup.send(f"Advanced dragon peek options have been sent to {user.mention} via DM.", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send(f"Could not send DM to {user.mention}. They might have DMs disabled.", ephemeral=True)
                logging.warning(f"Failed to send DM to {user}.")
        else:
            await interaction.followup.send(f"No cards left in the Dragon Deck to peek at!", ephemeral=True)
            logging.info(f"{interaction.user} tried advanced dragon peek but the Dragon Deck is empty.")

    class ConfirmView(discord.ui.View):
        """
        A View that presents buttons to confirm moving the top card to the bottom (now only used by advanced peek)
        """

        def __init__(self, user: discord.Member, admin_user: discord.Member, channel: discord.TextChannel, game_state: GameState, deck_key: str):
            super().__init__(timeout=60)  # Timeout after 60 seconds
            self.user = user
            self.admin_user = admin_user
            self.channel = channel
            self.game_state = game_state
            self.deck_key = deck_key

        @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
        async def yes(self, interaction_button: discord.Interaction, button: discord.ui.Button):
            """Handles the 'Yes' button press."""
            # Move the card to the bottom
            result = self.move_top_card_to_bottom(self.game_state, self.deck_key)
            try:
                await self.user.send(result)
            except discord.Forbidden:
                # User might have DMs disabled; handle gracefully
                pass
            # Send an ephemeral confirmation to the user interacting with the button
            await interaction_button.response.send_message("Your choice has been recorded.", ephemeral=True)
            self.stop()

        @discord.ui.button(label='No', style=discord.ButtonStyle.red)
        async def no(self, interaction_button: discord.Interaction, button: discord.ui.Button):
            """Handles the 'No' button press."""
            message = "Card remains at the top of the deck."
            try:
                await self.user.send(message)
            except discord.Forbidden:
                # User might have DMs disabled; handle gracefully
                pass
            await interaction_button.response.send_message("Your choice has been recorded and the card remains on the top.", ephemeral=True)
            self.stop()

        async def on_timeout(self):
            """Handles the timeout for the View."""
            message = "You took too long to respond. The card remains at the top of the deck."
            try:
                await self.user.send(message)
            except discord.Forbidden:
                pass
            # Notify the admin or game master about the timeout
            try:
                await self.admin_user.send(f"{self.user.display_name} did not respond in time to the advanced peek in {self.channel.mention}.")
            except discord.Forbidden:
                pass

        #Method to peak at top cards, used by advanced peek commands (event deck only)
        def move_top_card_to_bottom(self, game_state: GameState, deck_name: str) -> str:
            """
            Moves the top card of the specified deck to the bottom.
            """
            if deck_name in game_state.draw_piles and game_state.draw_piles[deck_name]:
                card = game_state.draw_piles[deck_name].pop()  # Remove the top card
                game_state.draw_piles[deck_name].insert(0, card)  # Insert it at the bottom
                return f"The card '{card['name']}' has been moved to the bottom of the {deck_name.replace('_', ' ').title()}."
            else:
                return "No cards left in the deck to move."
                
    #handles action for user of advanced dragon peek    
    class DragonPeekView(discord.ui.View):
        """
        A View for advanced dragon peek, allowing the user to destroy the top card of the draw pile and replace it with a 'There be Dragons card'.
        """

        def __init__(self, user: discord.Member, admin_user: discord.Member, channel: discord.TextChannel, game_state: GameState, deck_key: str, original_card: dict):
            super().__init__(timeout=60)
            self.user = user
            self.admin_user = admin_user
            self.channel = channel
            self.game_state = game_state
            self.deck_key = deck_key
            self.original_card = original_card

        @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
        async def yes(self, interaction_button: discord.Interaction, button: discord.ui.Button):
            """Handles the 'Yes' button press."""
            # Remove the top card (without putting it in the discard pile), ie destroying it
            self.game_state.draw_piles[self.deck_key].pop()

            # Find a copy of the 'There be Dragons!' card in the draw pile
            dragon_card = None
            # Search in draw pile
            for card in self.game_state.draw_piles[self.deck_key]:
                if card['name'].lower() == "there be dragons!":
                    dragon_card = card
                    break
            # If not found, search in discard pile
            if not dragon_card:
                for card in self.game_state.discard_piles[self.deck_key]:
                    if card['name'].lower() == "there be dragons!":
                        dragon_card = card
                        break
            # If found, create a copy and put it on top of the draw pile
            if dragon_card:
                self.game_state.draw_piles[self.deck_key].append(dragon_card)
                result_message = "A copy of the 'There be Dragons!' card has been added to the top of the draw pile."
            else:
                result_message = "Could not find an original 'There be Dragons!' card in the deck to copy."

            # Inform the user
            try:
                await self.user.send(result_message)
            except discord.Forbidden:
                pass
            await interaction_button.response.send_message("Your choice has been recorded.", ephemeral=True)
            self.stop()

        @discord.ui.button(label='No', style=discord.ButtonStyle.red)
        async def no(self, interaction_button: discord.Interaction, button: discord.ui.Button):
            """Handles the 'No' button press."""
            message = "No changes have been made to the Dragon Deck."
            try:
                await self.user.send(message)
            except discord.Forbidden:
                pass
            await interaction_button.response.send_message("Your choice has been recorded.", ephemeral=True)
            self.stop()

        async def on_timeout(self):
            """Handles the timeout for the View."""
            message = "You took too long to respond. No changes have been made."
            try:
                await self.user.send(message)
            except discord.Forbidden:
                pass
            # Notify the admin or game master about the timeout
            try:
                await self.admin_user.send(f"{self.user.display_name} did not respond in time to the advanced dragon peek in {self.channel.mention}.")
            except discord.Forbidden:
                pass

    #Method to peak at top cards, used by all peek commands.
    def peek_top_card(self, game_state: GameState, deck_name: str) -> Optional[Tuple[Dict[str, str], str]]:
        """
        Peeks at the top card of the specified deck without removing it.
        If the draw pile is empty, reshuffles the discard pile (and in-play cards from this deck) into the draw pile, then peeks.
        """
        if deck_name in game_state.draw_piles:
            if not game_state.draw_piles[deck_name]:
                # Draw pile is empty, need to reshuffle
                # Move discard pile into draw pile
                game_state.draw_piles[deck_name].extend(game_state.discard_piles[deck_name])
                game_state.discard_piles[deck_name].clear()
                logging.info(f"Moved discard pile of '{deck_name}' into draw pile for reshuffling.")
                
                # Now, move in-play cards from this deck into draw pile
                in_play_cards_to_remove = []
                for card_tuple in game_state.current_turn_drawn_cards:
                    card, card_deck_name = card_tuple
                    if card_deck_name == deck_name:
                        game_state.draw_piles[deck_name].append(card)
                        in_play_cards_to_remove.append(card_tuple)
                # Remove these cards from in_play_cards
                for card_tuple in in_play_cards_to_remove:
                    game_state.current_turn_drawn_cards.remove(card_tuple)
                logging.info(f"Moved in-play cards from '{deck_name}' back into draw pile for reshuffling.")

                # Shuffle the draw pile
                random.shuffle(game_state.draw_piles[deck_name])
                logging.info(f"Reshuffled the '{deck_name}' due to empty draw pile during peek.")
            
            if game_state.draw_piles[deck_name]:
                card = game_state.draw_piles[deck_name][-1]  # Peek at the top of the deck
                return card, deck_name
            else:
                # Even after reshuffling, the draw pile is empty
                logging.warning(f"No cards available in '{deck_name}' even after reshuffling.")
                return None
        else:
            logging.error(f"Deck '{deck_name}' does not exist in the game state.")
            return None