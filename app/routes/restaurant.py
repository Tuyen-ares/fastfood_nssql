from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, url_for
from app.models import Restaurant, Menu, Order, Review, User
from app.utils.auth import login_required, get_current_user
from app.utils.helpers import to_object_id
from app.database import get_db
from datetime import datetime
from bson import ObjectId
import os
from werkzeug.utils import secure_filename

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    """Save uploaded file and return URL"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        # Create directory if not exists
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Return URL path (relative to static)
        return url_for('static', filename=f'uploads/menus/{filename}')
    return None

@restaurant_bp.route('/dashboard')
@login_required
def dashboard():
    """Restaurant owner dashboard"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if approved
    user_status = user.get('status', '')
    if user_status not in ['approved', 'active']:
        flash('Tài khoản của bạn đang chờ admin duyệt. Vui lòng đợi thông báo.', 'warning')
        return render_template('restaurant/pending.html', user=user)
    
    # Get owner's restaurants
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào. Vui lòng đăng ký nhà hàng.', 'warning')
        return redirect(url_for('restaurant.register'))
    
    # Get statistics for first restaurant (or all restaurants)
    restaurant = restaurants[0] if restaurants else None
    stats = {}
    
    # Lấy doanh thu của chủ nhà hàng
    from app.utils.revenue import get_restaurant_owner_revenue
    owner_revenue = get_restaurant_owner_revenue(str(user['_id']))
    
    if restaurant:
        rest_id = restaurant['_id']
        stats = {
            'total_orders': get_db().orders.count_documents({'rest_id': rest_id}),
            'pending_orders': get_db().orders.count_documents({'rest_id': rest_id, 'status': 'pending'}),
            'preparing_orders': get_db().orders.count_documents({'rest_id': rest_id, 'status': 'preparing'}),
            'total_menus': get_db().menus.count_documents({'rest_id': rest_id}),
            'revenue': owner_revenue
        }
        
        # Get recent orders
        recent_orders = list(get_db().orders.find({'rest_id': rest_id}).sort('created_at', -1).limit(10))
    else:
        recent_orders = []
    
    return render_template('restaurant/dashboard.html',
                         user=user,
                         restaurant=restaurant,
                         restaurants=restaurants,
                         stats=stats,
                         orders=recent_orders)

@restaurant_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register new restaurant"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        addr = request.form.get('addr')
        open_time = request.form.get('open')
        close_time = request.form.get('close')
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        
        if not all([name, addr, open_time, close_time]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/register.html')
        
        # Create restaurant
        restaurant_data = {
            'name': name,
            'addr': addr,
            'open': open_time,
            'close': close_time,
            'owner_id': str(user['_id']),
            'status': 'pending',  # Chờ admin duyệt
            'rating': 0
        }
        
        if lat and lng:
            restaurant_data['loc'] = {
                'type': 'Point',
                'coordinates': [lng, lat]
            }
        
        Restaurant.create(restaurant_data)
        flash('Đã đăng ký nhà hàng thành công! Vui lòng chờ admin duyệt.', 'success')
        return redirect(url_for('restaurant.dashboard'))
    
    return render_template('restaurant/register.html')

@restaurant_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit restaurant information"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]  # Lấy nhà hàng đầu tiên
    
    if request.method == 'POST':
        name = request.form.get('name')
        addr = request.form.get('addr')
        open_time = request.form.get('open')
        close_time = request.form.get('close')
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        
        if not all([name, addr, open_time, close_time]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/edit.html', restaurant=restaurant)
        
        update_data = {
            'name': name,
            'addr': addr,
            'open': open_time,
            'close': close_time
        }
        
        if lat and lng:
            update_data['loc'] = {
                'type': 'Point',
                'coordinates': [lng, lat]
            }
        
        Restaurant.update(str(restaurant['_id']), update_data)
        flash('Đã cập nhật thông tin nhà hàng thành công', 'success')
        return redirect(url_for('restaurant.dashboard'))
    
    return render_template('restaurant/edit.html', restaurant=restaurant)

@restaurant_bp.route('/menus')
@login_required
def menus():
    """Manage menus"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    menus_list = Menu.find_by_restaurant(str(restaurant['_id']))
    
    return render_template('restaurant/menus.html',
                         restaurant=restaurant,
                         menus=menus_list)

@restaurant_bp.route('/menu/add', methods=['GET', 'POST'])
@login_required
def add_menu():
    """Add new menu item"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        
        # Handle file upload
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            uploaded_url = save_uploaded_file(uploaded_file)
            if uploaded_url:
                image_url = uploaded_url
            else:
                flash('File ảnh không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP', 'warning')
        
        if not all([name, price]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/menu_form.html', restaurant=restaurant)
        
        menu_data = {
            'rest_id': str(restaurant['_id']),
            'name': name,
            'price': price,
            'cat': category,
            'description': description,
            'image_url': image_url,
            'status': 'available'
        }
        
        Menu.create(menu_data)
        flash('Đã thêm món ăn thành công', 'success')
        return redirect(url_for('restaurant.menus'))
    
    return render_template('restaurant/menu_form.html', restaurant=restaurant)

@restaurant_bp.route('/menu/<menu_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_menu(menu_id):
    """Edit menu item"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    menu = Menu.find_by_id(menu_id)
    
    if not menu or str(menu['rest_id']) != str(restaurant['_id']):
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('restaurant.menus'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', menu.get('image_url', ''))
        status = request.form.get('status', 'available')
        
        # Handle file upload
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            uploaded_url = save_uploaded_file(uploaded_file)
            if uploaded_url:
                image_url = uploaded_url
            else:
                flash('File ảnh không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP', 'warning')
        
        if not all([name, price]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/menu_form.html', restaurant=restaurant, menu=menu)
        
        update_data = {
            'name': name,
            'price': price,
            'cat': category,
            'description': description,
            'image_url': image_url,
            'status': status
        }
        
        Menu.update(menu_id, update_data)
        flash('Đã cập nhật món ăn thành công', 'success')
        return redirect(url_for('restaurant.menus'))
    
    return render_template('restaurant/menu_form.html', restaurant=restaurant, menu=menu)

@restaurant_bp.route('/menu/<menu_id>/delete', methods=['POST'])
@login_required
def delete_menu(menu_id):
    """Delete menu item"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    menu = Menu.find_by_id(menu_id)
    
    if not menu or str(menu['rest_id']) != str(restaurant['_id']):
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('restaurant.menus'))
    
    Menu.delete(menu_id)
    flash('Đã xóa món ăn thành công', 'success')
    return redirect(url_for('restaurant.menus'))

@restaurant_bp.route('/reviews')
@login_required
def reviews():
    """View restaurant reviews"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    # Lấy tất cả reviews của các nhà hàng thuộc owner này
    all_reviews = []
    restaurant_filter = request.args.get('restaurant', '')
    rating_filter = request.args.get('rating', '')
    
    for restaurant in restaurants:
        # Lọc theo nhà hàng nếu có
        if restaurant_filter and str(restaurant['_id']) != restaurant_filter:
            continue
            
        rest_reviews = Review.find_by_restaurant(str(restaurant['_id']))
        for review in rest_reviews:
            # Lọc theo rating nếu có
            if rating_filter and str(review.get('restaurant_rating', '')) != rating_filter:
                continue
                
            review['restaurant'] = restaurant
            review['customer'] = User.find_by_id(str(review.get('user_id')))
            all_reviews.append(review)
    
    # Sắp xếp theo ngày mới nhất
    all_reviews.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    
    return render_template('restaurant/reviews.html', reviews=all_reviews, restaurants=restaurants)

@restaurant_bp.route('/orders')
@login_required
def orders():
    """View restaurant orders"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    status_filter = request.args.get('status', '')
    
    query = {'rest_id': restaurant['_id']}
    if status_filter:
        query['status'] = status_filter
    
    orders_list = list(get_db().orders.find(query).sort('created_at', -1))
    
    return render_template('restaurant/orders.html',
                         restaurant=restaurant,
                         orders=orders_list)

