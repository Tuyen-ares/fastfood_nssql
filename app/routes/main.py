from flask import Blueprint, render_template, url_for, request
from app.models import Menu, Restaurant
from app.database import get_db
from bson import ObjectId
from collections import defaultdict
import random

main_bp = Blueprint('main', __name__)

# Danh sách hình ảnh có sẵn (trừ logo)
AVAILABLE_IMAGES = [
    'bg3.webp',
    'bg5.jpg',
    'chicken.webp',
    'classic-shawarma.webp',
    'loaded-fries.webp',
    'pizza.webp',
    'spicy-wings.webp'
]

# Map category với hình ảnh phù hợp
CATEGORY_IMAGE_MAP = {
    'burger': ['chicken.webp', 'classic-shawarma.webp'],
    'pizza': ['pizza.webp'],
    'drink': ['bg3.webp'],
    'combo': ['loaded-fries.webp', 'chicken.webp'],
    'side': ['loaded-fries.webp', 'spicy-wings.webp'],
    'phở': ['classic-shawarma.webp'],
    'bánh mì': ['classic-shawarma.webp'],
    'cơm': ['chicken.webp'],
    'other': AVAILABLE_IMAGES
}

def get_menu_image(menu):
    """Lấy hình ảnh cho món ăn - ưu tiên image_url, sau đó map theo category"""
    # Nếu đã có image_url từ user upload, dùng luôn
    if menu.get('image_url'):
        return menu.get('image_url')
    
    # Nếu không có, map theo category
    category = menu.get('cat', 'other').lower()
    
    # Tìm hình ảnh phù hợp với category
    if category in CATEGORY_IMAGE_MAP:
        image_file = random.choice(CATEGORY_IMAGE_MAP[category])
    else:
        # Nếu category không có trong map, dùng random từ tất cả ảnh
        image_file = random.choice(AVAILABLE_IMAGES)
    
    return url_for('static', filename=f'img/{image_file}')

@main_bp.route('/')
def index():
    """Home page with menu items by category"""
    # Lấy tất cả món ăn từ các nhà hàng đã được duyệt
    approved_restaurants = Restaurant.find_all({'status': 'approved'})
    restaurant_ids = [str(r['_id']) for r in approved_restaurants]
    
    # Lấy tất cả món ăn available
    all_menus = []
    for rest_id in restaurant_ids:
        menus = Menu.find_by_restaurant(rest_id, {'status': 'available'})
        for menu in menus:
            menu['restaurant'] = Restaurant.find_by_id(rest_id)
            # Gán hình ảnh cho món ăn
            menu['display_image'] = get_menu_image(menu)
            all_menus.append(menu)
    
    # Nhóm món ăn theo category
    menus_by_category = defaultdict(list)
    for menu in all_menus:
        category = menu.get('cat', 'other')
        menus_by_category[category].append(menu)
    
    # Chuyển thành dict thông thường và sắp xếp
    menus_by_category = dict(sorted(menus_by_category.items()))

    # Lấy tham số lọc từ query string (ví dụ ?category=burger)
    category_filter = request.args.get('category', '').strip()

    # Danh sách tất cả categories (dùng để hiển thị nút lọc)
    all_categories = sorted(menus_by_category.keys())

    # Nếu có filter, chỉ giữ category đó
    if category_filter:
        filtered = {category_filter: menus_by_category.get(category_filter, [])}
        categories = filtered
    else:
        categories = menus_by_category

    return render_template('main/index.html', categories=categories, menus_by_category=menus_by_category, all_categories=all_categories, category=category_filter)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

