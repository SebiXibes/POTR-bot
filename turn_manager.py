# turn_manager.py

import discord
from discord.ext import commands
from discord import app_commands
import logging
from game_state import GameState
from card_mechanics import CardMechanics
from utils import admin_or_gamemaster_only, SHOW_PHASE_MESSAGES

class TurnManager(commands.Cog):
    """
    Discord commands related to turn advancement and phase processing.
    """

    def __init__(self, bot):
        self.bot = bot
        self.card_mechanics = CardMechanics(bot)
        
    @app_commands.command(name='nextturn', description='Advance the game to the next turn and execute phases.')
    @admin_or_gamemaster_only
    async def next_turn(self, interaction: discord.Interaction):
        """Advances the game to the next turn."""
        game_state = self.bot.game_states.get(interaction.channel_id)
        if not game_state:
            await interaction.response.send_message("No game is currently running in this channel.", ephemeral=False)
            return

        # Proceed with processing the next turn
        await interaction.response.defer(ephemeral=False)

        try:
            # Check if the game should end before processing the turn
            if game_state.end_game_flag:
                # Inform the user that the game has ended
                del self.bot.game_states[interaction.channel_id]
                await interaction.followup.send("**Game Over!** The game has ended.", ephemeral=False)
                logging.info(f"Game ended in channel {interaction.channel_id} after 'Time's Up!' was drawn.")
                return  # Do not process any further turns

            # Handle active views before advancing the turn
            active_views = game_state.active_views[:]
            for view in active_views:
                await view.on_turn_end()
            game_state.active_views.clear()

            # Advance to the next turn before processing
            game_state.advance_turn()

            # Process the turn
            await self.process_turn(interaction, game_state)

            # Do not end the game here; allow the game to continue even if end_game_flag was set during processing

        except Exception as e:
            logging.error(f"An unexpected error occurred during next_turn: {e}", exc_info=True)
            await interaction.followup.send("An error occurred while processing the next turn.", ephemeral=True)


    async def process_turn(self, interaction: discord.Interaction, game_state: GameState):
        """Processes the current turn."""
        # Phase 1: Protector Ranking (Placeholder)
        if SHOW_PHASE_MESSAGES:
            await interaction.followup.send(
                f"**Turn {game_state.current_turn} - Phase 1: Protector Ranking**\n*(Not implemented yet)*",
                ephemeral=False
            )
        logging.info(f"Executed Phase 1 for Turn {game_state.current_turn} in channel {interaction.channel_id}.")

        # Phase 2: Reveal Cards
        drawn_cards, black_swan_drawn = game_state.draw_cards_for_reveal_phase()
        if drawn_cards:
            await self.card_mechanics.handle_drawn_cards(interaction, game_state, drawn_cards, black_swan_drawn)
        else:
            await interaction.followup.send("No cards were drawn. All active decks are exhausted.", ephemeral=False)
            logging.info(f"No cards drawn for Phase 2 in Turn {game_state.current_turn} in channel {interaction.channel_id}.")

        # Future Phases: Placeholders
        if SHOW_PHASE_MESSAGES:
            phases = [
                "Phase 3: Negotiation and Orders *(Not implemented yet)*",
                "Phase 4: Execute Orders *(Not implemented yet)*",
                "Phase 5: Trading *(Not implemented yet)*",
                "Phase 6: Consolidation *(Not implemented yet)*"
            ]
            for phase in phases:
                await interaction.followup.send(phase, ephemeral=False)
                logging.info(f"Executed {phase} for Turn {game_state.current_turn} in channel {interaction.channel_id}.")
        else:
            logging.info(f"Skipped phase messages for Turn {game_state.current_turn} in channel {interaction.channel_id}.")

