import os
from dotenv import load_dotenv

# Path to the .env file in the current working directory
env_path = os.path.join(os.getcwd(), '.env')

# Load environment variables from the specific .env file
load_dotenv(dotenv_path=env_path)

# Define configuration variables
CLI_JSON_PATH = os.getenv("CLI_JSON_PATH", "cli.json")
DB_URI = os.getenv("DB_URI", "sqlite:///./database.db")
EXECUTABLE = os.getenv("EXECUTABLE", "./main") # Add this line for the executable config