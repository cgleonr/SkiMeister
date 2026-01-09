# SkiMeister 🎿

A modern web application to find nearby ski resorts with real-time snow conditions, filtering by distance, weather, pricing, and more.

![SkiMeister](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)

## Features

- 📍 **Geolocation-based search** - Automatically find ski resorts near you
- ❄️ **Real-time conditions** - Snow depth, fresh snowfall, temperature, wind speed
- 🎿 **Advanced filtering** - Filter by distance, snow conditions, price, open slopes
- 💰 **Price comparison** - Compare day pass prices across resorts
- 🌐 **Worldwide coverage** - Starting with Swiss Alps, expandable to all regions
- ⚡ **Fast local database** - SQLite for quick access to cached resort data
- 🎨 **Premium UI** - Modern dark theme with glassmorphism and smooth animations

## Tech Stack

**Backend:**
- Python 3.8+
- Flask (Web framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- BeautifulSoup4 (Web scraping)
- Geopy (Distance calculations)

**Frontend:**
- Vanilla HTML5, CSS3, JavaScript
- Modern CSS (Grid, Flexbox, CSS Variables)
- Geolocation API
- Fetch API for async requests

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd "c:/Users/carlo/OneDrive/Desktop/Personal Projects/SkiMeister"
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize and seed the database:**
   ```bash
   python seed_database.py
   ```
   This will create the SQLite database and populate it with sample Swiss resort data.

## Usage

### Starting the Server

1. **Run the Flask application:**
   ```bash
   python app.py
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

3. **Allow location permission** when prompted to find nearby resorts

### Using the Application

- **Search nearby resorts:** The app automatically finds resorts within 200km of your location
- **Adjust filters:** Use the sliders to filter by:
  - Distance (10-500 km)
  - Minimum snow depth (0-300 cm)
  - Maximum ticket price (0-200 CHF)
  - Minimum open slopes (0-400 km)
- **Sort results:** Sort by distance, name, snow depth, or price
- **View details:** Click on any resort card to see full details

## Project Structure

```
SkiMeister/
├── app.py                 # Flask application & API routes
├── config.py              # Configuration settings
├── database.py            # Database initialization & management
├── models.py              # SQLAlchemy models (Resort, Conditions, Pricing)
├── seed_database.py       # Database seeding script
├── requirements.txt       # Python dependencies
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py    # Base scraper with caching & rate limiting
│   └── bergfex_scraper.py # Bergfex-specific scraper
├── static/
│   ├── css/
│   │   └── style.css      # Premium UI styles
│   └── js/
│       └── app.js         # Main application logic
├── templates/
│   └── index.html         # Main page template
└── cache/                 # Cached scraper data (auto-created)
```

## API Endpoints

### Get All Resorts
```
GET /api/resorts
```
Returns all resorts with optional filters.

### Search Nearby Resorts
```
GET /api/search?lat={lat}&lng={lng}&radius={km}
```
Parameters:
- `lat` (required): User latitude
- `lng` (required): User longitude
- `radius` (optional): Search radius in km (default: 200)
- `min_snow` (optional): Minimum snow depth in cm
- `max_price` (optional): Maximum ticket price
- `min_slopes` (optional): Minimum open slopes in km
- `sort` (optional): Sort by distance, name, snow, or price

### Get Resort Details
```
GET /api/resort/{id}
```
Returns detailed information for a specific resort.

### Get Statistics
```
GET /api/stats
```
Returns database statistics (total resorts, countries).

## Database Schema

### Resort
- Basic info: name, slug, country, region
- Location: latitude, longitude
- Altitude: min/max elevation
- Website and description

### Conditions
- Snow: depth (valley/mountain), fresh snow (24h/48h)
- Weather: temperature, wind speed, visibility
- Slopes: open/total km, lifts open/total
- Status: open/closed/partial

### Pricing
- Adult/child day pass prices
- Currency
- Season start/end dates

## Development

### Adding More Resorts

To add more resorts, you can:

1. **Extend the scraper** - Add methods to scrape from additional sources
2. **Add data manually** - Create resort dictionaries and add via database session
3. **Import from CSV** - Create an import script for bulk data

### Scraper Development

The base scraper (`base_scraper.py`) includes:
- Rate limiting (configurable delay between requests)
- Caching (24-hour cache by default)
- Retry logic with exponential backoff
- User agent rotation

Extend `BergfexScraper` or create new scrapers for other data sources.

## Future Enhancements

- [ ] Live webcam feeds
- [ ] Weather forecast integration
- [ ] User reviews and ratings
- [ ] Favorite resorts
- [ ] Multi-day itinerary planner
- [ ] Mobile app (React Native)
- [ ] Social sharing features
- [ ] Trail maps integration

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - Feel free to use for personal or educational purposes.

## Acknowledgments

- Resort data inspired by bergfex.com
- Built with modern web technologies
- Designed for ski enthusiasts ⛷️

---

**Made with ❤️ for the skiing community**
