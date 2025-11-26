"""
Configuration management for test agent

Loads environment variables including API keys using python-dotenv
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API configuration from environment
JUNTOSS_API_KEY = os.getenv("JUNTOSS_API_KEY")
JUNTOSS_API_URL = os.getenv("JUNTOSS_API_URL", "http://localhost:8080")