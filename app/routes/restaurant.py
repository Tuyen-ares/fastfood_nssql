from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, url_for
from app.models import Restaurant, Menu, Order, Review, User, Voucher
from app.utils.auth import login_required, get_current_user
from app.utils.helpers import to_object_id
from app.database import get_db
from datetime import datetime
from bson import ObjectId
import os
from werkzeug.utils import secure_filename

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

def prepare_restaurants_for_template(restaurants, selected_restaurant=None):
    """
    Helper function to convert restaurants ObjectId to string for template comparison
    Returns: tuple (restaurants_with_ids, selected_rest_id_str)
    """
    selected_rest_id_str = str(selected_restaurant['_id']) if selected_restaurant else None
    restaurants_with_ids = []
    for rest in restaurants:
        rest_dict = dict(rest)
        rest_dict['_id_str'] = str(rest['_id'])
        restaurants_with_ids.append(rest_dict)
    return restaurants_with_ids, selected_rest_id_str

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
    
    # Get selected restaurant from query param or use first one
    selected_rest_id = request.args.get('rest_id', '')
    restaurant = None
    
    if selected_rest_id:
        # Validate that the restaurant belongs to this owner
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    # If no valid restaurant selected, use first one
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    stats = {}
    recent_orders = []
    
    # Lấy doanh thu của chủ nhà hàng (tổng tất cả nhà hàng)
    from app.utils.revenue import get_restaurant_owner_revenue
    owner_revenue = get_restaurant_owner_revenue(str(user['_id']))
    
    if restaurant:
        rest_id = restaurant['_id']
        stats = {
            'total_orders': get_db().orders.count_documents({'rest_id': rest_id}),
            'pending_orders': get_db().orders.count_documents({'rest_id': rest_id, 'status': 'pending'}),
            'preparing_orders': get_db().orders.count_documents({'rest_id': rest_id, 'status': 'preparing'}),
            'total_menus': get_db().menus.count_documents({'rest_id': rest_id}),
            'revenue': owner_revenue  # Tổng doanh thu của tất cả nhà hàng
        }
        
        # Get recent orders for selected restaurant
        recent_orders = list(get_db().orders.find({'rest_id': rest_id}).sort('created_at', -1).limit(10))
    
    # Convert ObjectId to string for template comparison
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    
    return render_template('restaurant/dashboard.html',
                         user=user,
                         restaurant=restaurant,
                         restaurants=restaurants_with_ids,
                         selected_rest_id_str=selected_rest_id_str,
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
    
    # Get selected restaurant from query param
    selected_rest_id = request.args.get('rest_id', '')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    if request.method == 'POST':
        # Check if restaurant is approved before allowing edit
        if restaurant.get('status') != 'approved':
            flash('Chỉ có thể chỉnh sửa nhà hàng đã được duyệt', 'warning')
            return redirect(url_for('restaurant.dashboard', rest_id=str(restaurant['_id'])))
        name = request.form.get('name')
        addr = request.form.get('addr')
        open_time = request.form.get('open')
        close_time = request.form.get('close')
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        
        if not all([name, addr, open_time, close_time]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
            return render_template('restaurant/edit.html', restaurant=restaurant, restaurants=restaurants_with_ids, selected_rest_id_str=selected_rest_id_str)
        
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
        return redirect(url_for('restaurant.dashboard', rest_id=str(restaurant['_id'])))
    
    return render_template('restaurant/edit.html', restaurant=restaurant, restaurants=restaurants)

@restaurant_bp.route('/delete/<rest_id>', methods=['POST'])
@login_required
def delete_restaurant(rest_id):
    """Delete restaurant"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurant = Restaurant.find_by_id(rest_id)
    if not restaurant:
        flash('Nhà hàng không tồn tại', 'danger')
        return redirect(url_for('restaurant.dashboard'))
    
    if str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền xóa nhà hàng này', 'danger')
        return redirect(url_for('restaurant.dashboard'))
    
    # Check if restaurant has pending orders
    pending_orders = get_db().orders.count_documents({
        'rest_id': restaurant['_id'],
        'status': {'$in': ['pending', 'preparing', 'delivering']}
    })
    
    if pending_orders > 0:
        flash('Không thể xóa nhà hàng đang có đơn hàng đang xử lý', 'danger')
        return redirect(url_for('restaurant.dashboard', rest_id=rest_id))
    
    # Delete all menus of this restaurant
    get_db().menus.delete_many({'rest_id': restaurant['_id']})
    
    # Delete all vouchers of this restaurant
    get_db().vouchers.delete_many({'rest_id': restaurant['_id']})
    
    # Delete restaurant
    get_db().restaurants.delete_one({'_id': restaurant['_id']})
    
    flash('Đã xóa nhà hàng thành công', 'success')
    return redirect(url_for('restaurant.dashboard'))

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
    
    # Get selected restaurant from query param
    selected_rest_id = request.args.get('rest_id', '')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    menus_list = Menu.find_by_restaurant(str(restaurant['_id']))
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/menus.html',
                         restaurant=restaurant,
                         restaurants=restaurants_with_ids,
                         selected_rest_id_str=selected_rest_id_str,
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
    
    # Get selected restaurant from query param or form
    selected_rest_id = request.args.get('rest_id') or request.form.get('rest_id')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
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
        return redirect(url_for('restaurant.menus', rest_id=str(restaurant['_id'])))
    
    return render_template('restaurant/menu_form.html', restaurant=restaurant, restaurants=restaurants)

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
    
    menu = Menu.find_by_id(menu_id)
    if not menu:
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('restaurant.menus'))
    
    # Find restaurant that owns this menu
    restaurant = Restaurant.find_by_id(str(menu['rest_id']))
    if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền chỉnh sửa món ăn này', 'danger')
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
        return redirect(url_for('restaurant.menus', rest_id=str(restaurant['_id'])))
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/menu_form.html', restaurant=restaurant, restaurants=restaurants_with_ids, selected_rest_id_str=selected_rest_id_str, menu=menu)

@restaurant_bp.route('/menu/<menu_id>/delete', methods=['POST'])
@login_required
def delete_menu(menu_id):
    """Delete menu item"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    menu = Menu.find_by_id(menu_id)
    if not menu:
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('restaurant.menus'))
    
    restaurant = Restaurant.find_by_id(str(menu['rest_id']))
    if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền xóa món ăn này', 'danger')
        return redirect(url_for('restaurant.menus'))
    
    Menu.delete(menu_id)
    flash('Đã xóa món ăn thành công', 'success')
    return redirect(url_for('restaurant.menus', rest_id=str(restaurant['_id'])))

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
    
    # Get selected restaurant from query param
    selected_rest_id = request.args.get('rest_id', '')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    status_filter = request.args.get('status', '')
    
    query = {'rest_id': restaurant['_id']}
    if status_filter:
        query['status'] = status_filter
    
    orders_list = list(get_db().orders.find(query).sort('created_at', -1))
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/orders.html',
                         restaurant=restaurant,
                         restaurants=restaurants_with_ids,
                         selected_rest_id_str=selected_rest_id_str,
                         orders=orders_list)

@restaurant_bp.route('/order/<order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    """Accept order by restaurant owner"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.find_by_id(order_id)
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Check if restaurant belongs to this owner
    restaurant = Restaurant.find_by_id(str(order.get('rest_id')))
    if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền chấp nhận đơn hàng này', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Check if restaurant is approved
    if restaurant.get('status') != 'approved':
        flash('Chỉ có thể chấp nhận đơn hàng khi nhà hàng đã được duyệt', 'warning')
        return redirect(url_for('restaurant.orders', rest_id=str(restaurant['_id'])))
    
    # Check if order is pending
    if order.get('status') != 'pending':
        flash('Đơn hàng này đã được xử lý', 'warning')
        return redirect(url_for('restaurant.orders', rest_id=str(restaurant['_id'])))
    
    # Update order status to preparing (chủ nhà hàng đã chấp nhận, chờ shipper)
    Order.update_status(order_id, 'preparing')
    
    flash('Đã chấp nhận đơn hàng thành công. Đơn hàng đang chờ shipper nhận.', 'success')
    return redirect(url_for('restaurant.orders', rest_id=str(restaurant['_id'])))

@restaurant_bp.route('/order/<order_id>/reject', methods=['POST'])
@login_required
def reject_order(order_id):
    """Reject order by restaurant owner"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.find_by_id(order_id)
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Check if restaurant belongs to this owner
    restaurant = Restaurant.find_by_id(str(order.get('rest_id')))
    if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền từ chối đơn hàng này', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Check if order is pending
    if order.get('status') != 'pending':
        flash('Đơn hàng này đã được xử lý', 'warning')
        return redirect(url_for('restaurant.orders', rest_id=str(restaurant['_id'])))
    
    # Update order status to cancelled
    Order.update_status(order_id, 'cancelled')
    
    flash('Đã từ chối đơn hàng', 'success')
    return redirect(url_for('restaurant.orders', rest_id=str(restaurant['_id'])))

@restaurant_bp.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """View order detail"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    order = Order.find_by_id(order_id)
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Check if restaurant belongs to this owner
    restaurant = Restaurant.find_by_id(str(order.get('rest_id')))
    if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
        flash('Bạn không có quyền xem đơn hàng này', 'danger')
        return redirect(url_for('restaurant.orders'))
    
    # Get customer info
    customer = User.find_by_id(str(order.get('user_id')))
    
    # Get payment info
    payment = Payment.find_by_order(order_id)
    
    # Get shipper info if exists
    shipper = None
    if order.get('shipper_id'):
        shipper = User.find_by_id(str(order.get('shipper_id')))
    
    # Build menu items
    menu_items = []
    if order.get('items'):
        for item in order.get('items', []):
            menu_items.append(item)
    
    return render_template('restaurant/order_detail.html',
                         order=order,
                         restaurant=restaurant,
                         customer=customer,
                         shipper=shipper,
                         payment=payment,
                         menu_items=menu_items)

@restaurant_bp.route('/vouchers')
@login_required
def vouchers():
    """Manage vouchers"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    # Get selected restaurant from query param
    selected_rest_id = request.args.get('rest_id', '')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    status_filter = request.args.get('status', '')
    
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    
    vouchers_list = Voucher.find_by_restaurant(str(restaurant['_id']), filters)
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/vouchers.html',
                         restaurant=restaurant,
                         restaurants=restaurants_with_ids,
                         selected_rest_id_str=selected_rest_id_str,
                         vouchers=vouchers_list)

@restaurant_bp.route('/voucher/add', methods=['GET', 'POST'])
@login_required
def add_voucher():
    """Add new voucher"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    # Get selected restaurant from query param or form
    selected_rest_id = request.args.get('rest_id') or request.form.get('rest_id')
    restaurant = None
    
    if selected_rest_id:
        restaurant = Restaurant.find_by_id(selected_rest_id)
        if not restaurant or str(restaurant.get('owner_id')) != str(user['_id']):
            flash('Nhà hàng không hợp lệ', 'danger')
            restaurant = None
    
    if not restaurant:
        restaurant = restaurants[0] if restaurants else None
    
    if not restaurant:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    menus_list = Menu.find_by_restaurant(str(restaurant['_id']))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        voucher_type = request.form.get('type', 'discount')
        discount_type = request.form.get('discount_type', 'percent')
        value = request.form.get('value', type=float)
        quantity = request.form.get('quantity', type=int)
        min_order_quantity = request.form.get('min_order_quantity', type=int, default=0)
        applicable_menu_ids = request.form.getlist('applicable_menu_ids')
        status = request.form.get('status', 'active')
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        
        if not all([code, value, quantity]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/voucher_form.html', restaurant=restaurant, menus=menus_list)
        
        # Kiểm tra code đã tồn tại chưa
        existing = Voucher.find_by_code(code, str(restaurant['_id']))
        if existing:
            flash('Mã voucher đã tồn tại', 'danger')
            return render_template('restaurant/voucher_form.html', restaurant=restaurant, menus=menus_list)
        
        voucher_data = {
            'rest_id': str(restaurant['_id']),
            'code': code,
            'type': voucher_type,
            'discount_type': discount_type if voucher_type == 'discount' else 'amount',
            'value': value,
            'quantity': quantity,
            'min_order_quantity': min_order_quantity or 0,
            'applicable_menu_ids': applicable_menu_ids if applicable_menu_ids else [],
            'status': status
        }
        
        if start_date_str:
            try:
                voucher_data['start_date'] = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            except:
                pass
        
        if end_date_str:
            try:
                voucher_data['end_date'] = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            except:
                pass
        
        Voucher.create(voucher_data)
        flash('Đã thêm voucher thành công', 'success')
        return redirect(url_for('restaurant.vouchers', rest_id=str(restaurant['_id'])))
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/voucher_form.html', restaurant=restaurant, restaurants=restaurants_with_ids, selected_rest_id_str=selected_rest_id_str, menus=menus_list)

@restaurant_bp.route('/voucher/<voucher_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_voucher(voucher_id):
    """Edit voucher"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    voucher = Voucher.find_by_id(voucher_id)
    
    if not voucher or str(voucher['rest_id']) != str(restaurant['_id']):
        flash('Voucher không tồn tại', 'danger')
        return redirect(url_for('restaurant.vouchers'))
    
    menus_list = Menu.find_by_restaurant(str(restaurant['_id']))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        voucher_type = request.form.get('type', 'discount')
        discount_type = request.form.get('discount_type', 'percent')
        value = request.form.get('value', type=float)
        quantity = request.form.get('quantity', type=int)
        min_order_quantity = request.form.get('min_order_quantity', type=int, default=0)
        applicable_menu_ids = request.form.getlist('applicable_menu_ids')
        status = request.form.get('status', 'active')
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        
        if not all([code, value, quantity]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('restaurant/voucher_form.html', restaurant=restaurant, menus=menus_list, voucher=voucher)
        
        # Kiểm tra code đã tồn tại chưa (trừ voucher hiện tại)
        existing = Voucher.find_by_code(code, str(restaurant['_id']))
        if existing and str(existing['_id']) != voucher_id:
            flash('Mã voucher đã tồn tại', 'danger')
            return render_template('restaurant/voucher_form.html', restaurant=restaurant, menus=menus_list, voucher=voucher)
        
        update_data = {
            'code': code,
            'type': voucher_type,
            'discount_type': discount_type if voucher_type == 'discount' else 'amount',
            'value': value,
            'quantity': quantity,
            'min_order_quantity': min_order_quantity or 0,
            'applicable_menu_ids': applicable_menu_ids if applicable_menu_ids else [],
            'status': status
        }
        
        if start_date_str:
            try:
                update_data['start_date'] = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            except:
                pass
        else:
            update_data['start_date'] = None
        
        if end_date_str:
            try:
                update_data['end_date'] = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            except:
                pass
        else:
            update_data['end_date'] = None
        
        Voucher.update(voucher_id, update_data)
        flash('Đã cập nhật voucher thành công', 'success')
        return redirect(url_for('restaurant.vouchers', rest_id=str(restaurant['_id'])))
    
    restaurants_with_ids, selected_rest_id_str = prepare_restaurants_for_template(restaurants, restaurant)
    return render_template('restaurant/voucher_form.html', restaurant=restaurant, restaurants=restaurants_with_ids, selected_rest_id_str=selected_rest_id_str, menus=menus_list, voucher=voucher)

@restaurant_bp.route('/voucher/<voucher_id>/delete', methods=['POST'])
@login_required
def delete_voucher(voucher_id):
    """Delete voucher"""
    user = get_current_user()
    if not user or user.get('role') != 'restaurant_owner':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    restaurants = Restaurant.find_by_owner(str(user['_id']))
    if not restaurants:
        flash('Bạn chưa có nhà hàng nào', 'warning')
        return redirect(url_for('restaurant.register'))
    
    restaurant = restaurants[0]
    voucher = Voucher.find_by_id(voucher_id)
    
    if not voucher or str(voucher['rest_id']) != str(restaurant['_id']):
        flash('Voucher không tồn tại', 'danger')
        return redirect(url_for('restaurant.vouchers'))
    
    restaurant = Restaurant.find_by_id(str(voucher['rest_id']))
    Voucher.delete(voucher_id)
    flash('Đã xóa voucher thành công', 'success')
    return redirect(url_for('restaurant.vouchers', rest_id=str(restaurant['_id']) if restaurant else ''))

