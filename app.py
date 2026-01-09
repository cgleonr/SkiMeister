"""
SkiMeister Flask API
"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from geopy.distance import geodesic
from sqlalchemy import or_
import config
from database import get_session, init_db
from models import Resort, Conditions, Pricing


app = Flask(__name__)
app.config.from_object(config)
CORS(app)


# Helper functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates"""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def apply_filters(query, filters):
    """Apply search filters to query"""
    
    # Filter by minimum snow depth
    if 'min_snow' in filters and filters['min_snow']:
        query = query.join(Conditions).filter(
            Conditions.snow_depth_mountain >= int(filters['min_snow'])
        )
    
    # Filter by status (open/closed)
    if 'status' in filters and filters['status']:
        query = query.join(Conditions).filter(
            Conditions.status == filters['status']
        )
    
    # Filter by minimum open slopes
    if 'min_slopes' in filters and filters['min_slopes']:
        query = query.join(Conditions).filter(
            Conditions.slopes_open_km >= float(filters['min_slopes'])
        )
    
    # Filter by max ticket price
    if 'max_price' in filters and filters['max_price']:
        query = query.join(Pricing).filter(
            Pricing.adult_day_pass <= float(filters['max_price'])
        )
    
    # Filter by country
    if 'country' in filters and filters['country']:
        query = query.filter(Resort.country == filters['country'])
    
    return query


# Routes
@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@app.route('/api/resorts', methods=['GET'])
def get_all_resorts():
    """Get all resorts with optional filters"""
    session = get_session()
    
    try:
        query = session.query(Resort)
        
        # Apply filters from query params
        filters = request.args.to_dict()
        query = apply_filters(query, filters)
        
        resorts = query.all()
        
        # Convert to dict
        result = [resort.to_dict() for resort in resorts]
        
        return jsonify({
            'success': True,
            'count': len(result),
            'resorts': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@app.route('/api/search', methods=['GET'])
def search_resorts():
    """
    Search for nearby resorts based on user location
    Query params:
    - lat: user latitude
    - lng: user longitude
    - radius: search radius in km (default: 200)
    - Other filters: min_snow, max_price, status, min_slopes
    """
    session = get_session()
    
    try:
        # Get user location
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if lat is None or lng is None:
            return jsonify({
                'success': False,
                'error': 'Missing lat or lng parameters'
            }), 400
        
        # Get radius
        radius = request.args.get('radius', config.DEFAULT_SEARCH_RADIUS_KM, type=float)
        radius = min(radius, config.MAX_SEARCH_RADIUS_KM)
        radius = max(radius, config.MIN_SEARCH_RADIUS_KM)
        
        # Get all resorts and calculate distances
        query = session.query(Resort)
        
        # Apply other filters
        filters = request.args.to_dict()
        query = apply_filters(query, filters)
        
        all_resorts = query.all()
        
        # Calculate distances and filter by radius
        nearby_resorts = []
        for resort in all_resorts:
            distance = calculate_distance(lat, lng, resort.latitude, resort.longitude)
            if distance <= radius:
                resort_dict = resort.to_dict()
                resort_dict['distance_km'] = round(distance, 1)
                nearby_resorts.append(resort_dict)
        
        # Sort by distance
        sort_by = request.args.get('sort', 'distance')
        
        if sort_by == 'distance':
            nearby_resorts.sort(key=lambda x: x['distance_km'])
        elif sort_by == 'name':
            nearby_resorts.sort(key=lambda x: x['name'])
        elif sort_by == 'price':
            nearby_resorts.sort(key=lambda x: x.get('pricing', {}).get('adult_day_pass', 999))
        elif sort_by == 'snow':
            nearby_resorts.sort(key=lambda x: x.get('conditions', {}).get('snow_depth_mountain', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(nearby_resorts),
            'user_location': {'lat': lat, 'lng': lng},
            'radius_km': radius,
            'resorts': nearby_resorts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@app.route('/api/resort/<int:resort_id>', methods=['GET'])
def get_resort(resort_id):
    """Get detailed information for a specific resort"""
    session = get_session()
    
    try:
        resort = session.query(Resort).filter(Resort.id == resort_id).first()
        
        if not resort:
            return jsonify({
                'success': False,
                'error': 'Resort not found'
            }), 404
        
        return jsonify({
            'success': True,
            'resort': resort.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    session = get_session()
    
    try:
        total_resorts = session.query(Resort).count()
        countries = session.query(Resort.country).distinct().all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_resorts': total_resorts,
                'countries': [c[0] for c in countries]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    print(f"\n🎿 SkiMeister API Server")
    print(f"Running on http://{config.HOST}:{config.PORT}")
    print(f"Press Ctrl+C to stop\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
