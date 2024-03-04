import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Use an environment variable for the API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable in a .env file.")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Base directory for the project
BASE_DIR = Path(__file__).parent

def get_file_path(directory, file_name, extension=''):
    """
    Constructs a file path for a given directory, file name, and extension.
    Ensures that the directory exists.
    """
    # Ensure the directory exists
    full_path = BASE_DIR / directory
    full_path.mkdir(parents=True, exist_ok=True)

    # Construct and return the full file path
    if file_name:  # If file_name is not empty
        return full_path / f"{file_name}.{extension}"
    else:
        return full_path