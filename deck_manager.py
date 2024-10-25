# deck_manager.py

import os
import json
import logging
from typing import List, Tuple, Dict, Optional
from utils import sanitize_input

class DeckManager:
    """
    Manages deck operations including creating, deleting, adding, and removing cards.
    Decks are stored as JSON files in the decks/ directory.
    """

    def __init__(self):
        self.decks_directory = 'decks'
        os.makedirs(self.decks_directory, exist_ok=True)
        self.decks = self.load_all_deck_keys()

    def load_all_deck_keys(self) -> Dict[str, Dict]:
        """
        Loads all decks from the decks directory.
        Each deck is expected to have a 'type', 'original_name', and a list of 'cards'.
        """
        decks = {}
        for filename in os.listdir(self.decks_directory):
            if filename.endswith('.json'):
                deck_key = filename[:-5]
                try:
                    with open(os.path.join(self.decks_directory, filename), 'r') as file:
                        data = json.load(file)
                        deck_type = data.get('type', 'custom')
                        original_name = data.get('original_name', deck_key)
                        decks[deck_key] = {
                            'type': deck_type,
                            'original_name': original_name,
                            'cards': data.get('cards', [])
                        }
                        logging.info(f"Loaded deck '{original_name}' of type '{deck_type}' with {len(decks[deck_key]['cards'])} cards.")
                except (json.JSONDecodeError, IOError) as e:
                    logging.error(f"Failed to load deck '{deck_key}': {e}")
        return decks

    def save_deck(self, deck_key: str) -> None:
        """
        Saves a specific deck to its JSON file.
        Includes type, original name, and list of cards.
        """
        try:
            with open(os.path.join(self.decks_directory, f"{deck_key}.json"), 'w') as file:
                json.dump({
                    'type': self.decks[deck_key]['type'],
                    'original_name': self.decks[deck_key]['original_name'],
                    'cards': self.decks[deck_key]['cards']
                }, file, indent=4)
            logging.info(f"Deck '{self.decks[deck_key]['original_name']}' of type '{self.decks[deck_key]['type']}' saved with {len(self.decks[deck_key]['cards'])} cards.")
        except IOError as e:
            logging.error(f"Failed to save deck '{deck_key}': {e}")

    def create_deck(self, deck_name: str, deck_type: str) -> Tuple[bool, str]:
        """
        Creates a new deck with the given name and type.
        Allows multiple decks of the same predefined type.
        Returns a tuple of (success: bool, message: str).
        """
        deck_key = sanitize_input(deck_name)
        deck_type = sanitize_input(deck_type).lower()

        if deck_key in self.decks:
            logging.warning(f"Attempted to create duplicate deck '{deck_key}'.")
            return False, "A deck with this name already exists."

        predefined_types = ['event_deck', 'dragon_deck', 'sea_deck', 'end_deck']
        if deck_type not in predefined_types:
            logging.error(f"Invalid deck type '{deck_type}' provided.")
            return False, f"Invalid deck type. Choose from: {', '.join(predefined_types)}."

        self.decks[deck_key] = {
            'type': deck_type,
            'original_name': deck_name,
            'cards': []
        }
        self.save_deck(deck_key)
        logging.info(f"Deck '{deck_name}' of type '{deck_type}' created.")
        return True, "Deck created successfully."

    def delete_deck(self, deck_name: str) -> Tuple[bool, str]:
        """
        Deletes a deck with the given name.
        Prevents deletion of required predefined decks.
        Returns a tuple of (success: bool, message: str).
        """
        deck_key = sanitize_input(deck_name)
        predefined_types = ['event_deck', 'dragon_deck', 'sea_deck', 'end_deck']

        if deck_key not in self.decks:
            logging.error(f"Attempted to delete non-existent deck '{deck_key}'.")
            return False, "Deck does not exist."

        del self.decks[deck_key]
        try:
            os.remove(os.path.join(self.decks_directory, f"{deck_key}.json"))
            logging.info(f"Deck '{deck_key}' deleted.")
            return True, "Deck deleted successfully."
        except OSError as e:
            logging.error(f"Failed to delete deck '{deck_key}': {e}")
            return False, "Failed to delete deck due to an error."

    def add_card_to_deck(self, deck_name: str, card: Dict[str, str]) -> Tuple[bool, str]:
        """
        Adds a card to a specific deck.
        Allows duplicate cards.
        Returns a tuple of (success: bool, message: str).
        """
        deck_key = sanitize_input(deck_name)
        if deck_key not in self.decks:
            logging.error(f"Attempted to add card to non-existent deck '{deck_name}'.")
            return False, "Deck does not exist."

        self.decks[deck_key]['cards'].append({
            'name': card['name'],
            'image': card['image']
        })
        self.save_deck(deck_key)
        logging.info(f"Card '{card['name']}' added to deck '{self.decks[deck_key]['original_name']}'.")
        return True, "Card added successfully."

    def remove_card_from_deck(self, deck_name: str, card_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        Removes a card from a specific deck by name.
        Returns a tuple of (success: bool, message: str, image_path: Optional[str]).
        """
        deck_key = sanitize_input(deck_name)
        if deck_key not in self.decks:
            logging.error(f"Attempted to remove card from non-existent deck '{deck_key}'.")
            return False, "Deck does not exist.", None

        for card in self.decks[deck_key]['cards']:
            if card['name'].strip().lower() == card_name.strip().lower():
                self.decks[deck_key]['cards'].remove(card)
                image_path = card.get('image')
                self.save_deck(deck_key)
                logging.info(f"Card '{card_name}' removed from deck '{self.decks[deck_key]['original_name']}'.")
                return True, f"Card '{card_name}' removed from deck '{self.decks[deck_key]['original_name']}'.", image_path

        logging.warning(f"Attempted to remove non-existent card '{card_name}' from deck '{deck_name}'.")
        return False, f"Card '{card_name}' does not exist in deck '{self.decks[deck_key]['original_name']}'.", None

    def get_deck_cards(self, deck_name: str) -> Optional[List[Dict[str, str]]]:
        """
        Retrieves all cards from a specific deck.
        """
        deck_key = sanitize_input(deck_name)
        if deck_key in self.decks:
            return self.decks[deck_key]['cards']
        return None

    def get_deck_type(self, deck_name: str) -> Optional[str]:
        """
        Retrieves the type of a specific deck.
        """
        deck_key = sanitize_input(deck_name)
        if deck_key in self.decks:
            return self.decks[deck_key]['type']
        return None

    def get_original_deck_name(self, deck_key: str) -> str:
        """
        Retrieves the original name of a deck based on its sanitized key.
        """
        if deck_key in self.decks:
            return self.decks[deck_key]['original_name']
        return deck_key
    
    def get_deck_key(self, deck_name: str) -> Optional[str]:
        """
        Returns the deck key corresponding to the provided deck name, ignoring case and spaces.
        """
        deck_name_normalized = sanitize_input(deck_name)
        for key, deck in self.decks.items():
            original_name_normalized = sanitize_input(deck['original_name'])
            if deck_name_normalized == original_name_normalized:
                return key
        return None