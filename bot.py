#bot.py

import os
import json
import asyncio
import discord
from discord.ext import commands
from game_state import GameState
from deck_manager import DeckManager
from deck_management_commands import DeckManagementCommands
from game_commands import GameCommands
from turn_manager import TurnManager
from peek_commands import PeekCommands
from utils import intents
from config import BOT_TOKEN
from logging_config import configure_logging

configure_logging()

class MyBot(commands.Bot):
    """Main bot class that initializes DeckManager and manages game states."""

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.deck_manager = DeckManager()
        self.game_states = {}  # Channel ID to GameState mapping
        self.lock = asyncio.Lock()  # Ensure thread-safe operations
        self.game_states_file = 'game_states.json'
        self.load_game_states()

    def load_game_states(self):
        """
        Loads game states from the game_states.json file.
        """
        if os.path.exists(self.game_states_file):
            try:
                with open(self.game_states_file, 'r') as file:
                    game_states_data = json.load(file)
                    for channel_id, state_data in game_states_data.items():
                        channel_id_int = int(channel_id)
                        deck_keys = state_data.get('deck_keys', [])
                        missing_decks = [deck for deck in deck_keys if deck not in self.deck_manager.decks]
                        if missing_decks:
                            missing_original = [self.deck_manager.get_original_deck_name(deck) for deck in missing_decks]
                            logging.warning(
                                f"Missing decks for channel {channel_id}: {', '.join(missing_original)}. Skipping this game state."
                            )
                            continue
                        try:
                            # Create a new GameState instance with the saved data
                            game_state = GameState(
                                channel_id=channel_id_int,
                                deck_keys=deck_keys,
                                deck_manager=self.deck_manager
                            )
                            # Restore game state attributes
                            game_state.draw_piles = state_data.get('draw_piles', {})
                            game_state.discard_piles = state_data.get('discard_piles', {})
                            game_state.current_turn = state_data.get('current_turn', 1)
                            game_state.keep_cards = state_data.get('keep_cards', []) #cards that are kept this turn due to end is nigh
                            game_state.end_game_flag = state_data.get('end_game_flag', False)
                            game_state.keep_current_turn_cards = state_data.get('keep_current_turn_cards', False) #whether keep cards flag is in on
                            game_state.current_turn_drawn_cards = state_data.get('current_turn_drawn_cards', []) #list of cards currently in play
                            self.game_states[channel_id_int] = game_state
                            logging.info(f"Restored game state for channel {channel_id}.")

                        except ValueError as e:
                            logging.error(f"Error restoring game state for channel {channel_id}: {e}")
                logging.info("Game states loaded.")
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Failed to load game states: {e}")

    async def save_game_states(self):
        """
        Saves all game states to the game_states.json file atomically.
        """
        async with self.lock:
            game_states_data = {}
            for channel_id, game_state in self.game_states.items():
                game_states_data[str(channel_id)] = {
                    'deck_keys': game_state.all_deck_keys,
                    'draw_piles': game_state.draw_piles,
                    'discard_piles': game_state.discard_piles,
                    'current_turn': game_state.current_turn,
                    'keep_cards': game_state.keep_cards,
                    'end_game_flag': game_state.end_game_flag,
                    'keep_current_turn_cards': game_state.keep_current_turn_cards,
                    'current_turn_drawn_cards': game_state.current_turn_drawn_cards,
                }
            temp_file = self.game_states_file + ".tmp"
            try:
                with open(temp_file, 'w') as file:
                    json.dump(game_states_data, file, indent=4)
                os.replace(temp_file, self.game_states_file)
                logging.info("Game states saved atomically.")
            except IOError as e:
                logging.error(f"Failed to save game states: {e}")

    async def setup_hook(self):
        """Sets up the bot by adding cogs and syncing the command tree."""
        await self.add_cog(DeckManagementCommands(self))
        await self.add_cog(GameCommands(self))
        await self.add_cog(TurnManager(self))
        await self.add_cog(PeekCommands(self))
        await self.tree.sync()
        logging.info("Command tree synced.")

    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        """Event handler called when an application command is successfully completed."""
        logging.info(f"Command '{command.name}' executed by {interaction.user} in {interaction.channel}.")
        await self.save_game_states()

    async def on_ready(self):
        """Event handler called when the bot is ready."""
        print(f'Logged in as {self.user.name}')
        logging.info(f'Logged in as {self.user.name}')

    async def close(self):
        """Ensures that game states are saved before the bot shuts down."""
        await self.save_game_states()
        logging.info("Bot is shutting down. Game states saved.")
        await super().close()

# Initialize and run the bot
if __name__ == '__main__':
    import logging

    client = MyBot()

    # Global error handler
    @client.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        """Handles errors globally for all application commands."""
        if interaction.response.is_done():
            await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)
        logging.error(f"An error occurred: {error}", exc_info=True)

    client.run(BOT_TOKEN)
