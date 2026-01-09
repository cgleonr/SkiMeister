"""
Configuration settings for SkiMeister application
"""
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, 'skimeister.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Scraper settings
SCRAPER_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]
SCRAPER_RATE_LIMIT = 2  # seconds between requests
SCRAPER_TIMEOUT = 30  # request timeout in seconds
SCRAPER_MAX_RETRIES = 3

# Cache settings
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
CACHE_EXPIRY_HOURS = 24  # Cache scraped data for 24 hours

# Search settings
DEFAULT_SEARCH_RADIUS_KM = 200  # Default radius for "day trip" distance
MAX_SEARCH_RADIUS_KM = 500
MIN_SEARCH_RADIUS_KM = 10

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)
