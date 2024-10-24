#config.py

import os
from dotenv import load_dotenv

# Read the bot token from '.env'

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in environment variables.")
