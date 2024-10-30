# Discord Card Game Bot

## Overview

Welcome to the **Discord Protectors of the Realm Card Game Bot**! This POTR-bot facilitates an engaging card game experience within Discord servers for the POTR-game, allowing admins, game masters and players to interact seamlessly through intuitive commands and dynamic game mechanics. Discord's slash command functionality is used.

---
## Key Components and Features
**Deck Management**
Deck Types: The bot supports predefined deck types such as event_deck, dragon_deck, sea_deck, and end_deck.

**CRUD Operations:**
Create/Delete Deck: Admins can create/delete new decks, specifying their type. 
Add/Remove Cards: Admins can add cards to decks by specifying the card name and uploading an associated image. Cards can also be removed based on their names.
Case Insensitivity: All deck and card names are sanitized to lowercase to ensure case-insensitive operations, preventing duplication and ensuring consistency across commands.

---
### Game State Management (GameState Class)

**Per-Channel Game States:** Each Discord channel can host its own game, with the bot maintaining separate game states to allow multiple concurrent games. After each action, the game states are saved automatically in a json file. in the event the bot crashes, the game states can be recovered

---
**Tracking Mechanisms**
Draw Piles & Discard Piles & In-play pile: Each active deck within a game has its own draw, in-play and discard piles, enabling dynamic card management throughout the game.
Turn Management: The bot tracks the current turn, advancing it as the game progresses with

**Initial Turn Setup:** 
Upon starting a new game with /startgame, the bot automatically draws and plays two specific cards:
"Calms of Summer" from the Event Deck.
"The Misty Mountains Cold" from the Dragon Deck.

---
**End Deck Functionality:**
"The End is Nigh!": When drawn, this card ensures that all other cards remain in play until the game concludes, effectively retaining their state across turns. Special care has been taken to make sure the interaction with the "Black Swan" swan card is correct.
"Time's Up!": Triggers the game to end after the current turn, enforcing game termination based on in-game events.

---
**Peeking.** Mechanics that allows the admin/GM to instruct the bot to send a card via DM to a specified player. This is basically the Kelu'ak ability. The peek command works on the Event Deck. The admin does not get to see the contents of the card, only that sending has been succesful. 'Advanced peek' allows the player who peeked at the card to place it at the bottom of the draw pile. Dragon peek allows the targeted player to look at the dragon deck. Advanced dragon peek lets the player discard a non attack card and replace it with an attack card.

--- 
**The "Black Swan" card.** This card will initiate the bot to shuffle the deck and draw a new card in the same turn. Special care was taken to make sure it works in tandem with the end is nigh! card

---
**Phases.** Each turn has several phases. Drawing cards happens in the second phase. For now, only placeholders for the other phases have been included, allowing for future expansion of the bot to fully manage the game.

## Future Work
The next recommended steps to further expand bot functionality:
- **Register players to a game inside a channel, including their classes**
- **Realm/resource management of each player**


## Detailed Features

- **Deck Management:** Create, modify, and view multiple card decks.
- **Game Control:** Start games, manage  turns, and monitor game status.
- **Card Interaction:** Peek at top cards, send cards via DM, and handle special card mechanics.
- **Persistent Game States:** Maintains game progress across bot restarts using persistent storage.
- **Admin & Game Master Commands:** Exclusive commands for admins to manage decks, and admin / game masters to manage games.
- **Player interaction:** Player get DMs sent by the bot for the Kelu'ak abilities (peek commands). Players can also check the contents of (fresh) decks using the appropriate deck commands.
- **User-Friendly UI:** Interactive Discord UI components like buttons for enhanced user experience.
- **Robust Logging:** Comprehensive logging for monitoring bot activities and debugging.

## Setup Instructions

### Prerequisites

- **Python 3.8+**: Ensure you have Python installed. You can download it [here](https://www.python.org/downloads/). (Was Developed on Python 3.12.3. Newer python versions were not compatible with discord library at time of testing (3.13)
- **Discord Bot Token**: Create a Discord bot and obtain its token. Follow the [Discord Developer Portal](https://discord.com/developers/applications) to set up your bot.

### Install Dependencies

It's recommended to use a virtual environment. recommended is to use a code editor such as visual code, and install the python extension. this allows to easily create virtual environments to projects.

### Configure the Bot

Bot Token: Add your Discord bot token to .env file. see the .env.example file as example (rename it to .env and include your discord token).

### Decks and Cards:
Cards are uploaded and deleted via the discord bot. But this can also manually be done by adding corresponding files to the /Cards folder, and updating the /decks/<deck_name>.json files

### Run the Bot
make sure the virtual environment is active. then run:
python bot.py
The bot should now be online and ready to use in your Discord server.


---
## Detailed Features

**Initial Turn Setup:** Upon starting a new game with /startgame, the bot automatically draws and plays two specific cards:
"Calms of Summer" from the Event Deck.
"The Misty Mountains Cold" from the Dragon Deck.

**End Deck Functionality:**
"The End is Nigh!": When drawn, this card ensures that all other cards remain in play until the game concludes, effectively retaining their state across turns.
"Time's Up!": Triggers the game to end after the current turn, enforcing game termination based on in-game events.

**Peeking.** Mechanics that allows the admin/GM to instruct the bot to send a card via DM to a specified player. This is basically the Kelu'ak ability. The peek command works on the Event Deck. The admin does not get to see the contents of the card, only that sending has been succesful. 'Advanced peek' allows the player who peeked at the card to place it at the bottom of the draw pile. Dragon peek allows the targeted player to look at the dragon deck. advanced dragon peek lets the player discard a non attack card and replace it with an attack card. When two players peek simultaneously, there is special mechanics that deals with how this is resolved.
 
**The "Black Swan" card.** This card will initiate the bot to shuffle the deck and draw a new card in the same turn. Special care was taken to make sure it works in tandem with the end is nigh! card.


---
## Usage
Start a Game: Use **/startgame** to initiate a new game.

Advance Turns: Use **/nextturn** to proceed to the next turn.

Check Game Status: Use **/status** to view the current game state.

List Cards in a Deck: Use **/listcards** with appropriate options to view cards.

/**peek**: Allows an admin to send the top card of the event deck privately to a specified user via Direct Message (DM). The admin only gets confirmation that the peek was successful, but not what the card is
/**advancedpeek**: Similar to peek, but the specified user can choose to move the top card to the bottom of the deck via interactive buttons in the DM.
/**dragonpeek**: Allows an admin to send the top card of the dragon deck privately to a specified user via Direct Message (DM). The admin only gets confirmation that the dragonpeek was successful, but not what the card is
/**advanceddragonpeek**: Similar to dragonpeek, but the specified user can choose to destroy the non-attack card and replace it with a There be dragons! card.


**and more!** (documentation in for future)

---

## Detailed File Descriptions
bot.py
The main script that launches the Discord bot. It initializes the bot instance, loads all command cogs, handles global events (e.g., on_ready, on_message), and starts the bot using the provided token.

card_mechanics.py
Handles all functionalities related to card operations within the game, such as  moving cards between different positions in a deck, and managing any special mechanics associated with specific cards.

config.py
Stores configuration settings and constants used throughout the bot, default deck names, game settings, and other parameters that might need to be adjusted without modifying the core code.

deck_manager.py
Manages the creation, organization, and manipulation of multiple card decks. It loads deck configurations from JSON files, shuffles decks, and provides interfaces to interact with different decks during the game.

deck_management_commands.py
Contains Discord command definitions related to managing decks. These commands allow admins or authorized users to perform actions like creating new decks, modifying existing ones, viewing deck contents, and other deck-related operations.

game_commands.py
Houses general game-related commands that players can use to interact with the game. This includes commands to start a game, join a game, leave a game, view game status, and perform in-game actions.

game_state.py
Defines the GameState class, which encapsulates the state of a game within a specific Discord channel. This includes tracking active decks, player turns, drawn cards, discarded cards, and other relevant game metrics.

game_states.json
Acts as a persistent storage medium for all active game states across different Discord channels. This JSON file ensures that game progress is saved and can be resumed in case the bot restarts or encounters issues.

peek_commands.py (PeekCommands cog)
Contains the implementation of the /peek and /advancedpeek Discord commands. These commands allow admins to peek at the top card of the event_deck and optionally move it to the bottom based on user interactions.

requirements.txt
Lists all Python packages and their respective versions required to run the bot. This ensures that the environment is set up correctly with all necessary dependencies.

.env
Securely stores the Discord bot token. Important: This file should be kept private and excluded from version control systems (e.g., by adding it to .gitignore) to prevent unauthorized access.see .env.example on how the content should look like. Add your bot token in the example and remove ".example"

turn_manager.py
Manages the flow of turns within the game, including determining the order of player turns, handling phase transitions, and ensuring that game rules are enforced during each turn.

utils.py
Provides a collection of utility functions and helper methods used across multiple modules and cogs. This includes functions like create_embed, sanitize_input, and admin checks.

logging_config.py
Sets up and configures the logging framework for the bot. This includes defining log formats, log levels, and handlers to direct logs to appropriate destinations like bot.log.

decks/
Directory containing JSON files that define the structure and content of different card decks used in the game. Each JSON file typically represents a separate deck with its own set of cards and rules.

Cards/
Directory storing image files for each card. These images are used in Discord embeds to visually represent cards when they are peeked at or drawn by players.

bot.log
Log file capturing all bot activities, errors, and important events for debugging and monitoring purposes.
