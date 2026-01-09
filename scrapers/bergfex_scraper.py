"""
Bergfex scraper for ski resort data
"""
import re
from scrapers.base_scraper import BaseScraper


class BergfexScraper(BaseScraper):
    """Scraper for bergfex.com ski resort data"""
    
    BASE_URL = "https://www.bergfex.com"
    
    def get_resort_list(self, country='schweiz'):
        """
        Get list of resorts for a country
        Countries: schweiz, oesterreich, italien, deutschland, frankreich
        """
        url = f"{self.BASE_URL}/{country}/skigebiete/"
        
        html = self.fetch_url(url)
        if not html:
            return []
        
        soup = self.parse_html(html)
        resorts = []
        
        # Bergfex lists resorts in various ways, but usually as links with specific classes
        # Based on browser research, a common pattern is a.js-track.tw-group
        links = soup.select('a.js-track')
        if not links:
            # Fallback to general links containing '/ski/'
            links = soup.find_all('a', href=re.compile(r'/[^/]+/ski/'))
            
        seen_urls = set()
        for link in links:
            href = link.get('href')
            if not href:
                continue
                
            # Clean URL: ensure it's the base resort URL
            # Standard pattern: /resort-slug/
            match = re.match(r'^/([^/]+)/$', href)
            if not match:
                # Try to extract from /resort-slug/ski/
                match = re.match(r'^/([^/]+)/ski/.*', href)
            
            if match:
                slug = match.group(1)
                resort_url = f"{self.BASE_URL}/{slug}/"
                
                if resort_url not in seen_urls:
                    name_elem = link.find('span') or link
                    name = name_elem.get_text(strip=True)
                    
                    if name and len(name) > 2:
                        resorts.append({
                            'name': name,
                            'slug': slug,
                            'url': resort_url,
                            'country': country.capitalize()
                        })
                        seen_urls.add(resort_url)
        
        return resorts
    
    def scrape_resort(self, resort_url):
        """Scrape detailed information for a specific resort"""
        html = self.fetch_url(resort_url)
        if not html:
            return None
        
        soup = self.parse_html(html)
        data = {
            'url': resort_url,
            'conditions': {},
            'pricing': {},
            'forecasts': []
        }
        
        try:
            # 1. Basic Info
            title_elem = soup.find('h1')
            if title_elem:
                data['name'] = title_elem.get_text(strip=True)
            
            # 2. Coordinates from JSON-LD
            import json
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    js_data = json.loads(script.string)
                    # Check if it's a list or a single object
                    items = js_data if isinstance(js_data, list) else [js_data]
                    for item in items:
                        if item.get('@type') == 'SkiResort' or 'geo' in item:
                            geo = item.get('geo', {})
                            if geo:
                                data['latitude'] = float(geo.get('latitude'))
                                data['longitude'] = float(geo.get('longitude'))
                            
                            if 'description' in item:
                                data['description'] = item['description'][:1000]
                            
                            if 'address' in item:
                                data['region'] = item['address'].get('addressRegion')
                except (json.JSONDecodeError, TypeError, ValueError, KeyError):
                    continue

            # 3. Altitude
            altitude_elem = soup.findAll(string=re.compile(r'(\d+)m\s*-\s*(\d+)m'))
            if altitude_elem:
                match = re.search(r'(\d+)m\s*-\s*(\d+)m', altitude_elem[0])
                if match:
                    data['altitude_min'] = int(match.group(1))
                    data['altitude_max'] = int(match.group(2))

            # 4. Snow conditions (Current Information section)
            snow_info = soup.find('div', string=re.compile(r'Current information|Current snow report', re.I))
            if not snow_info:
                # Search for specific labels
                mountain_label = soup.find(string=re.compile(r'Mountain:', re.I))
                if mountain_label:
                    mountain_val = mountain_label.find_parent().find_next_sibling()
                    if mountain_val:
                        match = re.search(r'(\d+)', mountain_val.get_text())
                        if match:
                            data['conditions']['snow_depth_mountain'] = int(match.group(1))
                
                valley_label = soup.find(string=re.compile(r'Valley:', re.I))
                if valley_label:
                    valley_val = valley_label.find_parent().find_next_sibling()
                    if valley_val:
                        match = re.search(r'(\d+)', valley_val.get_text())
                        if match:
                            data['conditions']['snow_depth_valley'] = int(match.group(1))

            # 5. Status
            status_elem = soup.select_one('.resort-status, .status-label')
            if status_elem:
                status_text = status_elem.get_text(strip=True).lower()
                if 'open' in status_text:
                    data['conditions']['status'] = 'open'
                elif 'closed' in status_text:
                    data['conditions']['status'] = 'closed'
                else:
                    data['conditions']['status'] = 'partial'

            # 6. Scrape Forecast
            forecast_data = self.scrape_forecast(resort_url)
            if forecast_data:
                data['forecasts'] = forecast_data

            return data
            
        except Exception as e:
            print(f"Error parsing resort data from {resort_url}: {e}")
            return None

    def scrape_forecast(self, resort_url):
        """Scrape 7-day weather forecast"""
        forecast_url = f"{resort_url.rstrip('/')}/wetter/prognose/"
        html = self.fetch_url(forecast_url)
        if not html:
            return []
        
        soup = self.parse_html(html)
        forecasts = []
        
        try:
            # Forecast is usually in a container with class .forecast9d
            container = soup.select_one('.forecast9d-container, .forecast9d')
            if not container:
                return []
            
            days = container.select('.day')
            from datetime import datetime, timedelta
            current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for i, day_el in enumerate(days[:7]):  # Get 7 days
                forecast = {
                    'date': current_date + timedelta(days=i)
                }
                
                # Temperatures
                # Usually there are mountain and valley temps. We'll take mountain or max/min.
                temps = day_el.select('.temp')
                if temps:
                    # Often structure is: Max, Min
                    vals = [float(re.search(r'(-?\d+)', t.get_text()).group(1)) for t in temps if re.search(r'(-?\d+)', t.get_text())]
                    if len(vals) >= 2:
                        forecast['temp_max'] = max(vals)
                        forecast['temp_min'] = min(vals)
                
                # Snowfall
                snow_el = day_el.select_one('.snow, .fresh-snow')
                if snow_el:
                    snow_match = re.search(r'(\d+)', snow_el.get_text())
                    if snow_match:
                        forecast['snow_forecast_cm'] = int(snow_match.group(1))
                else:
                    forecast['snow_forecast_cm'] = 0
                
                # Symbol/Icon
                img = day_el.find('img')
                if img:
                    # Extract symbol name from img src or title
                    # e.g., .../symbols/w1.png -> sunny
                    src = img.get('src', '')
                    forecast['symbol'] = os.path.basename(src).split('.')[0]
                
                forecasts.append(forecast)
                
            return forecasts
        except Exception as e:
            print(f"Error parsing forecast from {forecast_url}: {e}")
            return []
    
    def get_sample_resorts_switzerland(self):
        """
        Return sample Swiss ski resort data for initial development
        This provides structured data while we develop the full scraper
        """
        return [
            {
                'name': 'Zermatt - Matterhorn',
                'slug': 'zermatt-matterhorn',
                'country': 'Switzerland',
                'region': 'Valais',
                'latitude': 45.9763,
                'longitude': 7.7476,
                'altitude_min': 1620,
                'altitude_max': 3883,
                'website': 'https://www.zermatt.ch',
                'conditions': {
                    'snow_depth_valley': 25,
                    'snow_depth_mountain': 180,
                    'fresh_snow_24h': 5,
                    'temperature_valley': -3,
                    'temperature_mountain': -12,
                    'wind_speed': 15,
                    'visibility': 'good',
                    'slopes_open_km': 320,
                    'slopes_total_km': 360,
                    'lifts_open': 48,
                    'lifts_total': 52,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 89,
                    'child_day_pass': 45,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Verbier - 4 Vallées',
                'slug': 'verbier-4-vallees',
                'country': 'Switzerland',
                'region': 'Valais',
                'latitude': 46.0964,
                'longitude': 7.2282,
                'altitude_min': 1500,
                'altitude_max': 3330,
                'website': 'https://www.verbier.ch',
                'conditions': {
                    'snow_depth_valley': 30,
                    'snow_depth_mountain': 195,
                    'fresh_snow_24h': 10,
                    'temperature_valley': -2,
                    'temperature_mountain': -10,
                    'wind_speed': 20,
                    'visibility': 'good',
                    'slopes_open_km': 380,
                    'slopes_total_km': 410,
                    'lifts_open': 80,
                    'lifts_total': 92,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 82,
                    'child_day_pass': 41,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'St. Moritz',
                'slug': 'st-moritz',
                'country': 'Switzerland',
                'region': 'Graubünden',
                'latitude': 46.4908,
                'longitude': 9.8355,
                'altitude_min': 1720,
                'altitude_max': 3057,
                'website': 'https://www.stmoritz.ch',
                'conditions': {
                    'snow_depth_valley': 40,
                    'snow_depth_mountain': 165,
                    'fresh_snow_24h': 0,
                    'temperature_valley': -5,
                    'temperature_mountain': -11,
                    'wind_speed': 25,
                    'visibility': 'moderate',
                    'slopes_open_km': 280,
                    'slopes_total_km': 350,
                    'lifts_open': 54,
                    'lifts_total': 56,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 79,
                    'child_day_pass': 39,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Jungfrau - Grindelwald',
                'slug': 'jungfrau-grindelwald',
                'country': 'Switzerland',
                'region': 'Bern',
                'latitude': 46.6238,
                'longitude': 8.0411,
                'altitude_min': 943,
                'altitude_max': 2971,
                'website': 'https://www.jungfrau.ch',
                'conditions': {
                    'snow_depth_valley': 20,
                    'snow_depth_mountain': 210,
                    'fresh_snow_24h': 15,
                    'temperature_valley': -1,
                    'temperature_mountain': -9,
                    'wind_speed': 18,
                    'visibility': 'good',
                    'slopes_open_km': 200,
                    'slopes_total_km': 206,
                    'lifts_open': 42,
                    'lifts_total': 44,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 74,
                    'child_day_pass': 37,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Davos Klosters',
                'slug': 'davos-klosters',
                'country': 'Switzerland',
                'region': 'Graubünden',
                'latitude': 46.8029,
                'longitude': 9.8227,
                'altitude_min': 1124,
                'altitude_max': 2844,
                'website': 'https://www.davos.ch',
                'conditions': {
                    'snow_depth_valley': 35,
                    'snow_depth_mountain': 155,
                    'fresh_snow_24h': 8,
                    'temperature_valley': -4,
                    'temperature_mountain': -13,
                    'wind_speed': 22,
                    'visibility': 'good',
                    'slopes_open_km': 290,
                    'slopes_total_km': 300,
                    'lifts_open': 51,
                    'lifts_total': 53,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 76,
                    'child_day_pass': 38,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Laax',
                'slug': 'laax',
                'country': 'Switzerland',
                'region': 'Graubünden',
                'latitude': 46.8332,
                'longitude': 9.2607,
                'altitude_min': 1100,
                'altitude_max': 3018,
                'website': 'https://www.laax.com',
                'conditions': {
                    'snow_depth_valley': 45,
                    'snow_depth_mountain': 190,
                    'fresh_snow_24h': 12,
                    'temperature_valley': -3,
                    'temperature_mountain': -11,
                    'wind_speed': 16,
                    'visibility': 'excellent',
                    'slopes_open_km': 220,
                    'slopes_total_km': 224,
                    'lifts_open': 27,
                    'lifts_total': 28,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 81,
                    'child_day_pass': 40,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Engelberg-Titlis',
                'slug': 'engelberg-titlis',
                'country': 'Switzerland',
                'region': 'Central Switzerland',
                'latitude': 46.8237,
                'longitude': 8.4079,
                'altitude_min': 1050,
                'altitude_max': 3020,
                'website': 'https://www.engelberg.ch',
                'conditions': {
                    'snow_depth_valley': 50,
                    'snow_depth_mountain': 240,
                    'fresh_snow_24h': 20,
                    'temperature_valley': -2,
                    'temperature_mountain': -14,
                    'wind_speed': 28,
                    'visibility': 'moderate',
                    'slopes_open_km': 80,
                    'slopes_total_km': 82,
                    'lifts_open': 24,
                    'lifts_total': 25,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 73,
                    'child_day_pass': 36,
                    'currency': 'CHF'
                }
            },
            {
                'name': 'Arosa Lenzerheide',
                'slug': 'arosa-lenzerheide',
                'country': 'Switzerland',
                'region': 'Graubünden',
                'latitude': 46.7828,
                'longitude': 9.6759,
                'altitude_min': 1229,
                'altitude_max': 2865,
                'website': 'https://www.arosalenzerheide.swiss',
                'conditions': {
                    'snow_depth_valley': 28,
                    'snow_depth_mountain': 170,
                    'fresh_snow_24h': 3,
                    'temperature_valley': -6,
                    'temperature_mountain': -12,
                    'wind_speed': 19,
                    'visibility': 'good',
                    'slopes_open_km': 215,
                    'slopes_total_km': 225,
                    'lifts_open': 40,
                    'lifts_total': 43,
                    'status': 'open'
                },
                'pricing': {
                    'adult_day_pass': 77,
                    'child_day_pass': 38,
                    'currency': 'CHF'
                }
            }
        ]


if __name__ == '__main__':
    # Test the scraper
    scraper = BergfexScraper()
    resorts = scraper.get_sample_resorts_switzerland()
    print(f"Found {len(resorts)} sample resorts")
    for resort in resorts[:3]:
        print(f"- {resort['name']} ({resort['country']})")
