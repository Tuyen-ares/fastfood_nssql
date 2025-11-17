from bson import ObjectId
from datetime import datetime

def to_object_id(id_string):
    """Convert string to ObjectId"""
    try:
        return ObjectId(id_string)
    except:
        return None

def format_currency(amount):
    """Format number as Vietnamese currency"""
    return f"{amount:,.0f} đ".replace(',', '.')

def format_datetime(dt):
    """Format datetime to Vietnamese format"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt.strftime("%d/%m/%Y %H:%M")

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates (Haversine formula)"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r  # Distance in kilometers

def paginate(query, page, per_page=20):
    """Paginate query results"""
    skip = (page - 1) * per_page
    total = len(list(query.clone()))
    items = list(query.skip(skip).limit(per_page))
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }

