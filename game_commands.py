# game_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import logging
from game_state import GameState
from utils import admin_only, admin_or_gamemaster_only
from deck_manager import DeckManager

class GameCommands(commands.Cog):
    """
    Contains commands related to game management.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='startgame', description='Start a new game with the required decks.')
    @admin_or_gamemaster_only
    async def start_game(self, interaction: discord.Interaction):
        """Starts a new game in the current channel."""
        if interaction.channel_id in self.bot.game_states:
            await interaction.response.send_message(
                "A game is already running in this channel.",
                ephemeral=True
            )
            return

        # Get available decks for each type
        deck_types = ['event_deck', 'dragon_deck', 'sea_deck', 'end_deck']
        decks_by_type = {deck_type: [] for deck_type in deck_types}
        for deck_key, deck_info in self.bot.deck_manager.decks.items():
            if deck_info['type'] in deck_types:
                decks_by_type[deck_info['type']].append((deck_key, deck_info['original_name']))

        # Check if there is at least one deck of each type
        missing_decks = [deck_type for deck_type, decks in decks_by_type.items() if not decks]
        if missing_decks:
            missing_original = [deck_type.replace('_', ' ').title() for deck_type in missing_decks]
            await interaction.response.send_message(
                f"Missing deck(s) of type: {', '.join(missing_original)}. Please create them first.",
                ephemeral=True
            )
            return

        # Create selection menus for each deck type
        class DeckSelectionView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=60)
                self.bot = bot
                self.selected_decks = {}

                for deck_type in deck_types:
                    options = [
                        discord.SelectOption(label=name, value=key)
                        for key, name in decks_by_type[deck_type]
                    ]
                    select = discord.ui.Select(
                        placeholder=f"Select {deck_type.replace('_', ' ').title()}",
                        min_values=1,
                        max_values=1,
                        options=options
                    )
                    select.deck_type = deck_type

                    async def callback(interaction_select: discord.Interaction, select=select):
                        self.selected_decks[select.deck_type] = interaction_select.data['values'][0]
                        await interaction_select.response.defer()

                    select.callback = callback
                    self.add_item(select)

                confirm_button = discord.ui.Button(label='Start Game', style=discord.ButtonStyle.green)

                async def confirm(interaction_button: discord.Interaction):
                    if len(self.selected_decks) < len(deck_types):
                        await interaction_button.response.send_message("Please select a deck for each type.", ephemeral=True)
                        return
                    # Proceed to start the game
                    selected_deck_keys = list(self.selected_decks.values())
                    game_state = GameState(
                        channel_id=interaction_button.channel_id,
                        deck_keys=selected_deck_keys,
                        deck_manager=self.bot.deck_manager
                    )
                    self.bot.game_states[interaction_button.channel_id] = game_state

                    # Log game start
                    logging.info(f"{interaction_button.user} started a game in channel {interaction_button.channel_id}.")

                    # Send initial game start message
                    await interaction_button.response.send_message("**Game Started!** Beginning with Turn 1.", ephemeral=False)

                    # Process the first turn using TurnManager
                    turn_manager = self.bot.get_cog('TurnManager')
                    if turn_manager:
                        await turn_manager.process_turn(interaction_button, game_state)
                        # Do not call game_state.advance_turn() here
                    else:
                        logging.error("TurnManager cog not found.")
                    self.stop()

                confirm_button.callback = confirm
                self.add_item(confirm_button)

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                if hasattr(self, 'message'):
                    await self.message.edit(view=self)

        view = DeckSelectionView(self.bot)
        await interaction.response.send_message("Select decks to use for the game:", view=view, ephemeral=True)
        view.message = await interaction.original_response()


    @app_commands.command(name='endgame', description='End the current game in this channel.')
    @admin_or_gamemaster_only
    async def end_game(self, interaction: discord.Interaction):
        """Ends the game in the current channel."""
        if interaction.channel_id not in self.bot.game_states:
            await interaction.response.send_message("No game is currently running in this channel.", ephemeral=True)
            return

        # Confirmation view
        class ConfirmEndGameView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=30)
                self.bot = bot

            @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger)
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                del self.bot.game_states[interaction.channel_id]
                await interaction_button.response.send_message("Game ended in this channel.", ephemeral=True)
                logging.info(f"{interaction_button.user} ended the game in channel {interaction_button.channel_id}.")
                self.stop()

            @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                await interaction_button.response.send_message("Game end canceled.", ephemeral=True)
                self.stop()

            async def on_timeout(self):
                if not self.children[0].disabled:
                    await interaction.followup.send("Game end timed out. Please try again.", ephemeral=True)

        view = ConfirmEndGameView(self.bot)
        await interaction.response.send_message("Are you sure you want to end the current game?", view=view, ephemeral=True)

    @app_commands.command(name='status', description='Show the status of the current game.')
    @admin_or_gamemaster_only
    async def game_status(self, interaction: discord.Interaction):
        """Shows the status of the current game."""
        game_state = self.bot.game_states.get(interaction.channel_id)
        if game_state:
            status_message = f"**Turn {game_state.current_turn}**\n"
            active_decks = game_state.get_active_decks()
            status_message += f"**Active Decks:** {', '.join([self.bot.deck_manager.get_original_deck_name(deck) for deck in active_decks])}\n"
            for deck_name in active_decks:
                draw_count = len(game_state.draw_piles[deck_name])
                discard_count = len(game_state.discard_piles[deck_name])
                status_message += f"\n**Deck '{self.bot.deck_manager.get_original_deck_name(deck_name)}':**\nCards in draw pile: {draw_count}\nCards in discard pile: {discard_count}\n"
           
            # Include cards currently in play
            cards_in_play = game_state.keep_cards + game_state.current_turn_drawn_cards
            if cards_in_play:
                card_names = ', '.join([card['name'] for card, _ in cards_in_play])
                status_message += f"\n\n**Cards in Play:** {card_names}"
            else:
                status_message += "\n\n**Cards in Play:** None"

            if game_state.end_game_flag:
                status_message += "\n\n**Game will end after this turn.**"
            await interaction.response.send_message(status_message, ephemeral=True)
        else:
            await interaction.response.send_message("No game is currently running in this channel.", ephemeral=True)

