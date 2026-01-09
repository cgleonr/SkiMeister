"""
Database seeding script - populate with initial resort data
"""
from database import get_session, init_db
from models import Resort, Conditions, Pricing, Forecast
from scrapers.bergfex_scraper import BergfexScraper
from datetime import datetime


def add_resort_to_db(session, resort_data):
    """Add or update a resort and its associated data in the database"""
    # Check if resort already exists
    resort = session.query(Resort).filter(Resort.slug == resort_data['slug']).first()
    
    if not resort:
        resort = Resort(
            name=resort_data['name'],
            slug=resort_data['slug'],
            country=resort_data.get('country', 'Unknown'),
            region=resort_data.get('region'),
            latitude=resort_data.get('latitude', 0.0),
            longitude=resort_data.get('longitude', 0.0),
            altitude_min=resort_data.get('altitude_min'),
            altitude_max=resort_data.get('altitude_max'),
            website=resort_data.get('website'),
            description=resort_data.get('description')
        )
        session.add(resort)
        session.flush()
    else:
        # Update existing resort info
        resort.name = resort_data['name']
        resort.region = resort_data.get('region', resort.region)
        resort.latitude = resort_data.get('latitude', resort.latitude)
        resort.longitude = resort_data.get('longitude', resort.longitude)
        resort.altitude_min = resort_data.get('altitude_min', resort.altitude_min)
        resort.altitude_max = resort_data.get('altitude_max', resort.altitude_max)
        resort.description = resort_data.get('description', resort.description)
    
    # Update conditions
    if 'conditions' in resort_data and resort_data['conditions']:
        cond_data = resort_data['conditions']
        if not resort.conditions:
            resort.conditions = Conditions(resort_id=resort.id)
            session.add(resort.conditions)
            
        resort.conditions.snow_depth_valley = cond_data.get('snow_depth_valley')
        resort.conditions.snow_depth_mountain = cond_data.get('snow_depth_mountain')
        resort.conditions.fresh_snow_24h = cond_data.get('fresh_snow_24h')
        resort.conditions.temperature_valley = cond_data.get('temperature_valley')
        resort.conditions.temperature_mountain = cond_data.get('temperature_mountain')
        resort.conditions.status = cond_data.get('status', 'unknown')
        resort.conditions.last_updated = datetime.utcnow()
    
    # Update pricing
    if 'pricing' in resort_data and resort_data['pricing']:
        price_data = resort_data['pricing']
        if not resort.pricing:
            resort.pricing = Pricing(resort_id=resort.id)
            session.add(resort.pricing)
            
        resort.pricing.adult_day_pass = price_data.get('adult_day_pass')
        resort.pricing.child_day_pass = price_data.get('child_day_pass')
        resort.pricing.currency = price_data.get('currency', 'CHF')
        resort.pricing.last_updated = datetime.utcnow()
        
    # Update forecasts
    if 'forecasts' in resort_data and resort_data['forecasts']:
        # Delete old forecasts
        session.query(Forecast).filter(Forecast.resort_id == resort.id).delete()
        
        for f_data in resort_data['forecasts']:
            forecast = Forecast(
                resort_id=resort.id,
                date=f_data['date'],
                temp_min=f_data.get('temp_min'),
                temp_max=f_data.get('temp_max'),
                symbol=f_data.get('symbol'),
                snow_forecast_cm=f_data.get('snow_forecast_cm')
            )
            session.add(forecast)
            
    return resort


def seed_database(limit=None, country='switzerland'):
    """Seed the database with real resort data"""
    init_db()
    session = get_session()
    scraper = BergfexScraper()
    
    try:
        print(f"Fetching resort list for {country}...")
        resort_list = scraper.get_resort_list(country)
        
        if not resort_list:
            print(f"No resorts found for {country}.")
            return 0
            
        # If limit is None, scrape all resorts
        scrape_limit = limit if limit is not None else len(resort_list)
        print(f"Found {len(resort_list)} resorts. Scraping top {scrape_limit}...")
        
        count = 0
        for r_info in resort_list[:scrape_limit]:
            print(f"Scraping details for {r_info['name']}...")
            resort_data = scraper.scrape_resort(r_info['url'])
            if resort_data:
                resort_data['slug'] = r_info['slug']
                resort_data['country'] = r_info['country']
                add_resort_to_db(session, resort_data)
                count += 1
                if count % 5 == 0:
                    session.commit()
                    print(f"Safely committed {count} resorts...")
            
        session.commit()
        print(f"\n✓ Successfully seeded/updated {count} resorts!")
        return count
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        return 0
    finally:
        session.close()


if __name__ == '__main__':
    # Use a small limit for testing, or increase for full country
    import sys
    limit_arg = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(limit_arg) if limit_arg and limit_arg.isdigit() else None
    country = sys.argv[2] if len(sys.argv) > 2 else 'switzerland'
    seed_database(limit=limit, country=country)
