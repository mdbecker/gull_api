import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define configuration variables
CLI_JSON_PATH = os.getenv("CLI_JSON_PATH", "cli.json")
DB_URI = os.getenv("DB_URI", "sqlite:///./database.db")
