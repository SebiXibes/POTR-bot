# card_mechanics.py

import discord
import os
import uuid
import random
import logging
from typing import List, Tuple, Dict, Optional
from game_state import GameState

class CardMechanics:
    """
    Handles card drawing and special card mechanics.
    """

    def __init__(self, bot):
        self.bot = bot

    #Retrieves the cards that need to be sent to the discord bot for displaying
    async def handle_drawn_cards(self, interaction: discord.Interaction, game_state: GameState, drawn_cards: List[Tuple[dict, str]], black_swan_triggered: bool):
        """
        Handles the drawn cards during the reveal phase, including special card mechanics.
        """
        content = f"**Turn {game_state.current_turn} - Phase 2: Reveal Cards**"
        files = []
        embeds = []
        for idx, (card, deck_name) in enumerate(drawn_cards, start=1):
            embed = discord.Embed(title=card['name'])
            image_exists = os.path.exists(card['image'])
            if image_exists:
                file_extension = os.path.splitext(card['image'])[1]
                file_name = f"card_{uuid.uuid4().hex}{file_extension}"
                file = discord.File(card['image'], filename=file_name)
                embed.set_image(url=f"attachment://{file_name}")
                files.append(file)
            else:
                logging.warning(f"Image not found for card '{card['name']}'")
            embeds.append(embed)

        # Send the embeds and files in batches of 10 (discord cannot handle more)
        MAX_EMBEDS_PER_MESSAGE = 10
        total_embeds = len(embeds)
        for i in range(0, total_embeds, MAX_EMBEDS_PER_MESSAGE):
            batch_embeds = embeds[i:i + MAX_EMBEDS_PER_MESSAGE]
            batch_files = files[i:i + MAX_EMBEDS_PER_MESSAGE]
            if i == 0:
                await interaction.followup.send(content=content, files=batch_files, ephemeral=False)
            else:
                await interaction.followup.send(content=content, files=batch_files, ephemeral=False)

        # First, handle 'The End is Nigh!' and 'Time's Up!'
        for card, deck_name in drawn_cards:
            if card['name'].lower() in ["the end is nigh!", "time's up!"]:
                await self.handle_special_card(card, interaction, game_state) #if yes, execute special cards method
                logging.info(f"Processed special card '{card['name']}'. keep_current_turn_cards is now {game_state.keep_current_turn_cards}")

        # Then handle 'Black Swan'
        for card, deck_name in drawn_cards:
            if card['name'].lower() == "black swan":
                if not black_swan_triggered:
                    black_swan_triggered = True  # Trigger the effect
                if not game_state.keep_current_turn_cards:
                    # Move Black Swan to discard pile only if 'The End is Nigh!' is not active
                    game_state.current_turn_drawn_cards.remove((card, deck_name))
                    game_state.discard_piles[deck_name].append(card)
                    logging.info("Black Swan drawn: Moved to discard pile.")
                else:
                    logging.info("Black Swan drawn during 'The End is Nigh!': Kept in play.")
                black_swan_deck_name = deck_name

        # After handling all cards, process Black Swan effect if triggered
        if black_swan_triggered:
            await self.process_black_swan_effect(interaction, game_state, black_swan_deck_name)

    async def handle_special_card(self, card: dict, interaction: discord.Interaction, game_state: GameState):
        """
        Handles special card effects based on the card name.
        Updates the game state accordingly.
        """
        card_name = card['name'].lower()
        if card_name == "the end is nigh!":
            await interaction.followup.send(
                "**The End is Nigh! All other cards played this turn will remain in play until the game ends.**",
                ephemeral=False
            )
            game_state.set_keep_current_turn_cards(True)
        elif card_name == "time's up!":
            await interaction.followup.send(
                "**The game will end after this turn.**",
                ephemeral=False
            )
            game_state.set_end_game_flag(True)
        # Add more special card effects here as needed
        
    async def process_black_swan_effect(self, interaction: discord.Interaction, game_state: GameState, deck_name: str):
        """
        Processes the effect of 'Black Swan', reshuffling the Event Deck and drawing a new card.
        """
        while True:
            # Inform players about the Black Swan effect
            await interaction.followup.send(
                f"**Black Swan** effect triggered! The discard pile of '{game_state.deck_manager.get_original_deck_name(deck_name)}' has been reshuffled, and a new card is drawn.",
                ephemeral=False
            )

            # Reshuffle the Event Deck's discard pile back into the draw pile
            if game_state.discard_piles[deck_name]:
                game_state.draw_piles[deck_name].extend(game_state.discard_piles[deck_name])
                game_state.discard_piles[deck_name].clear()
                random.shuffle(game_state.draw_piles[deck_name])
                logging.info(f"Deck '{deck_name}' reshuffled due to Black Swan effect.")
            else:
                logging.warning(f"Discard pile of deck '{deck_name}' is empty during Black Swan effect.")

            # Draw a new card from the specified deck
            ## Check if draw piles are not empty
            if not game_state.draw_piles.get(deck_name):
                logging.warning(f"Deck '{deck_name}' is empty after reshuffling.")
                break  # Exit the loop if no cards are left
            ## Otherwise draw the new card from the draw pile and put it on the in play pile
            card = game_state.draw_piles[deck_name].pop()
            game_state.current_turn_drawn_cards.append((card, deck_name))
            
            # Send the new drawn card in a separate message
            embed = discord.Embed(title=f"A new card was drawn from '{game_state.deck_manager.get_original_deck_name(deck_name)}': {card['name']}")
            image_exists = os.path.exists(card['image'])
            if image_exists:
                file_extension = os.path.splitext(card['image'])[1]
                file_name = f"card_{uuid.uuid4().hex}{file_extension}"
                file = discord.File(card['image'], filename=file_name)
                embed.set_image(url=f"attachment://{file_name}")
                await interaction.followup.send(embed=embed, file=file, ephemeral=False)
            else:
                await interaction.followup.send(embed=embed, ephemeral=False)
                logging.warning(f"Image not found for card '{card['name']}'")

            # Then check if the new card is another Black Swan
            if card['name'].lower() == "black swan":
                if not game_state.keep_current_turn_cards:
                    # Move Black Swan to discard pile if 'The End is Nigh!' is not active
                    game_state.current_turn_drawn_cards.remove((card, deck_name))
                    game_state.discard_piles[deck_name].append(card)
                    logging.info(f"Another Black Swan drawn from '{deck_name}': Moved to discard pile.")
                else:
                    logging.info(f"Another Black Swan drawn from '{deck_name}' during 'The End is Nigh!': Kept in play.")
                # Continue the loop to process the effect again
                continue
            else:
                # Break out of the loop after processing non-Black Swan card
                break