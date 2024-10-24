# game_state.py

import random
import logging
from typing import List, Dict, Tuple, Optional
from deck_manager import DeckManager

class GameState:
    """
    Manages the state of a game within a Discord channel.
    Tracks active decks, draw and discard piles, current turn, kept cards, and end game flag.
    """

    def __init__(self, channel_id: int, deck_keys: List[str], deck_manager: DeckManager):
        self.channel_id = channel_id # In which channel the game is taking place
        self.deck_manager = deck_manager
        self.all_deck_keys = deck_keys  # All decks used in the game
        self.draw_piles: Dict[str, List[Dict[str, str]]] = {} #List of cards in the draw pile
        self.discard_piles: Dict[str, List[Dict[str, str]]] = {} # List of cards in the discard piles
        self.current_turn: int = 1  # Initialize to turn 1
        self.keep_cards: List[Tuple[Dict[str, str], str]] = [] # List of cards & decks kept from previous turn
        self.keep_current_turn_cards: bool = False #whether end is nigh! is active
        self.current_turn_drawn_cards: List[Tuple[Dict[str, str], str]] = [] #List of cards currently in play
        self.end_game_flag: bool = False #Whether this is the last turn

        for deck_key in self.all_deck_keys:
            deck_info = self.deck_manager.decks.get(deck_key)
            if deck_info is None:
                raise ValueError(f"Deck '{deck_key}' does not exist.")
            cards = deck_info['cards']
            # Use a deep copy to ensure original deck is not modified
            self.draw_piles[deck_key] = [card.copy() for card in cards]
            self.discard_piles[deck_key] = []
            random.shuffle(self.draw_piles[deck_key])
        logging.info(f"GameState initialized for channel {channel_id} with decks: {', '.join(deck_keys)}.")

    def draw_cards_for_reveal_phase(self) -> Tuple[List[Tuple[dict, str]], bool]:
        initial_drawn_cards = []
        black_swan_triggered = False  # Flag to indicate if Black Swan effect should trigger

        # Include kept cards from the previous turn
        if self.keep_cards:
            initial_drawn_cards.extend(self.keep_cards)
            self.current_turn_drawn_cards.extend(self.keep_cards)
            self.keep_cards = []  # Clear after including them

        # Check if 'Black Swan' is in play from previous turn (due to End is Nigh!) and set its trigger to 'True'
        black_swan_in_play = any(card['name'].lower() == "black swan" for card, _ in self.current_turn_drawn_cards)
        if black_swan_in_play:
            black_swan_triggered = True
            logging.info("Black Swan is in play from a previous turn.")

        # Proceed with drawing cards from active decks
        active_decks = self.get_active_decks()

        if self.current_turn == 1:
            # Handle special cards for Turn 1
            # Draw "Calms of Summer" from the Event Deck
            event_deck = next((deck for deck in active_decks if self.deck_manager.decks[deck]['type'] == 'event_deck'), None)
            if event_deck:
                calms_of_summer = next((card for card in self.draw_piles[event_deck] if card['name'].lower() == 'calms of summer'), None)
                if calms_of_summer:
                    self.draw_piles[event_deck].remove(calms_of_summer)
                    initial_drawn_cards.append((calms_of_summer, event_deck))
                    self.current_turn_drawn_cards.append((calms_of_summer, event_deck))
                else:
                    logging.warning("Calms of Summer not found in Event Deck.")
            else:
                logging.warning("No Event Deck active for Turn 1.")

            # Draw "The Misty Mountains Cold" from the Dragon Deck
            dragon_deck = next((deck for deck in active_decks if self.deck_manager.decks[deck]['type'] == 'dragon_deck'), None)
            if dragon_deck:
                misty_mountains_cold = next((card for card in self.draw_piles[dragon_deck] if card['name'].lower() == 'the misty mountains cold'), None)
                if misty_mountains_cold:
                    self.draw_piles[dragon_deck].remove(misty_mountains_cold)
                    initial_drawn_cards.append((misty_mountains_cold, dragon_deck))
                    self.current_turn_drawn_cards.append((misty_mountains_cold, dragon_deck))
                else:
                    logging.warning("The Misty Mountains Cold not found in Dragon Deck.")
            else:
                logging.warning("No Dragon Deck active for Turn 1.")
        else:
            # Regular card drawing for other turns
            for deck_name in active_decks:

                # Reshuffle the deck if the draw pile is empty
                if not self.draw_piles[deck_name]:
                    self.draw_piles[deck_name].extend(self.discard_piles[deck_name])
                    self.discard_piles[deck_name].clear()
                    random.shuffle(self.draw_piles[deck_name])

                # Draw one card from each active deck
                if self.draw_piles[deck_name]:
                    card = self.draw_piles[deck_name].pop()
                    initial_drawn_cards.append((card, deck_name))
                    self.current_turn_drawn_cards.append((card, deck_name))

                    # Check for Black Swans and set trigger to true if found
                    if deck_name == 'event_deck' and card['name'].lower() == "black swan":
                        black_swan_triggered = True
                        logging.info("Black Swan drawn: Effect will be processed.")

        # Return whether Black Swan's effect should be triggered
        return initial_drawn_cards, black_swan_triggered

    def get_active_decks(self) -> List[str]:
        """
        Determines which deck types are active, then finds the corresponding decks based on the current turn.
        """
        active_types = [] #Active based on type
        if self.current_turn >= 1:
            active_types.extend(['event_deck', 'dragon_deck'])
        if self.current_turn >= 5:
            active_types.append('sea_deck')
        if self.current_turn >= 10:
            active_types.append('end_deck')

        active_decks = [] #Find corresponding decks
        for deck_key in self.all_deck_keys:
            deck_type = self.deck_manager.decks[deck_key]['type']
            if deck_type in active_types:
                active_decks.append(deck_key)
        return active_decks

    def advance_turn(self) -> None:
        """
        Advances the game to the next turn, handling any necessary state updates.
        """
        # If 'The End is Nigh!' was drawn, keep the cards except 'The End is Nigh!' itself
        if self.keep_current_turn_cards:
            remaining_in_play = []
            for card, deck_name in self.current_turn_drawn_cards:
                if card['name'].lower() == "the end is nigh!":
                    self.discard_piles[deck_name].append(card)
                    logging.info("'The End is Nigh!' discarded at the end of the turn.")
                else:
                    remaining_in_play.append((card, deck_name))
                    logging.info(f"Card '{card['name']}' remains in play.")
            self.keep_cards = remaining_in_play
            logging.info(f"Cards from turn {self.current_turn} are kept for the next turn, excluding 'The End is Nigh!'.")
        else:
            # Normal play, move all in-play cards to discard piles
            for card, deck_name in self.current_turn_drawn_cards:
                self.discard_piles[deck_name].append(card)
                logging.info(f"Card '{card['name']}' moved to discard pile.")
            self.keep_cards.clear()
            logging.info(f"All in-play cards moved to discard piles at the end of turn {self.current_turn}.")

        # Clear the current_turn_drawn_cards for the next turn and reset the keep flag
        self.current_turn_drawn_cards.clear()
        self.keep_current_turn_cards = False

        self.current_turn += 1  # Increment the turn number
        logging.info(f"Advanced to turn {self.current_turn} in channel {self.channel_id}.")
    
    def set_keep_current_turn_cards(self, keep: bool = True) -> None:
        """
        Sets the flag to keep current turn's cards for the next turn.
        """
        self.keep_current_turn_cards = keep
        logging.info(f"Set keep_current_turn_cards to {self.keep_current_turn_cards}.")

    def set_end_game_flag(self, end_game: bool = True) -> None:
        """
        Sets the flag to end the game after the current turn.
        """
        self.end_game_flag = end_game
        logging.info(f"Set end_game_flag to {self.end_game_flag}.")
