"""
Base scraper class with rate limiting and caching
"""
import time
import random
import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import config


class BaseScraper:
    """Base scraper with common functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        
    def _get_user_agent(self):
        """Get a random user agent"""
        return random.choice(config.SCRAPER_USER_AGENTS)
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < config.SCRAPER_RATE_LIMIT:
            time.sleep(config.SCRAPER_RATE_LIMIT - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, key):
        """Get cache file path for a given key (URL), hashed for safety"""
        import hashlib
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return os.path.join(config.CACHE_DIR, f"{hashed_key}.json")
    
    def _get_cached(self, key):
        """Get cached data if not expired"""
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check expiry
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            expiry = timedelta(hours=config.CACHE_EXPIRY_HOURS)
            
            if datetime.utcnow() - cached_time < expiry:
                return cached_data['data']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        return None
    
    def _set_cached(self, key, data):
        """Cache data with timestamp"""
        cache_path = self._get_cache_path(key)
        
        cached_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cached_data, f, ensure_ascii=False, indent=2)
    
    def fetch_url(self, url, use_cache=True):
        """Fetch URL with rate limiting, retries, and caching"""
        
        # Check cache first
        if use_cache:
            cached = self._get_cached(url)
            if cached:
                return cached
        
        # Rate limit
        self._rate_limit()
        
        # Retry logic
        for attempt in range(config.SCRAPER_MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': self._get_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=config.SCRAPER_TIMEOUT
                )
                response.raise_for_status()
                
                # Cache the response
                if use_cache:
                    self._set_cached(url, response.text)
                
                return response.text
                
            except requests.RequestException as e:
                if attempt == config.SCRAPER_MAX_RETRIES - 1:
                    print(f"Failed to fetch {url} after {config.SCRAPER_MAX_RETRIES} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def parse_html(self, html):
        """Parse HTML with BeautifulSoup"""
        return BeautifulSoup(html, 'lxml')
