from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app, url_for as flask_url_for
from app.models import Restaurant, Menu, Order, Payment, User, Review
from app.utils.auth import login_required, get_current_user
from app.utils.helpers import to_object_id, format_currency, paginate
from app.utils.vnpay import VnPay
from app.database import get_db
from datetime import datetime
from werkzeug.utils import secure_filename
from bson import ObjectId
import os

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    """Customer dashboard"""
    user = get_current_user()
    if not user or user.get('role') != 'customer':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    # Get recent orders
    recent_orders = Order.find_by_user(str(user['_id']), limit=5)
    
    # Get active orders (preparing, delivering) for notifications
    active_orders = list(get_db().orders.find({
        'user_id': to_object_id(str(user['_id'])),
        'status': {'$in': ['preparing', 'delivering']}
    }).sort('updated_at', -1))
    
    return render_template('customer/dashboard.html', 
                         user=user, 
                         orders=recent_orders,
                         active_orders=active_orders)

@customer_bp.route('/restaurants')
@login_required
def restaurants():
    """List restaurants with category filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', 'approved')
    
    filters = {'status': status_filter}
    if search:
        filters['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'addr': {'$regex': search, '$options': 'i'}}
        ]
    
    restaurants = Restaurant.find_all(filters)
    
    # Nếu có filter category, chỉ hiển thị nhà hàng có món ăn thuộc category đó
    if category_filter:
        filtered_restaurants = []
        for rest in restaurants:
            menus = Menu.find_by_restaurant(str(rest['_id']), {'cat': category_filter, 'status': 'available'})
            if menus:
                filtered_restaurants.append(rest)
        restaurants = filtered_restaurants
    
    # Lấy tất cả categories từ menu items
    all_categories = set()
    for rest in restaurants:
        menus = Menu.find_by_restaurant(str(rest['_id']), {'status': 'available'})
        for menu in menus:
            if menu.get('cat'):
                all_categories.add(menu.get('cat'))
    
    # Simple pagination
    per_page = 12
    start = (page - 1) * per_page
    end = start + per_page
    paginated_restaurants = restaurants[start:end]
    
    return render_template('customer/restaurants.html',
                         restaurants=paginated_restaurants,
                         page=page,
                         search=search,
                         category=category_filter,
                         categories=sorted(all_categories),
                         total=len(restaurants))

@customer_bp.route('/restaurant/<rest_id>')
@login_required
def restaurant_detail(rest_id):
    """Restaurant detail with menu"""
    restaurant = Restaurant.find_by_id(rest_id)
    if not restaurant:
        flash('Nhà hàng không tồn tại', 'danger')
        return redirect(url_for('customer.restaurants'))
    
    # Get menus - filter only available
    menus = Menu.find_by_restaurant(rest_id, {'status': 'available'})
    
    # Import function từ main.py để gán hình ảnh
    from app.routes.main import get_menu_image
    
    # Gán hình ảnh cho mỗi menu item
    for menu in menus:
        menu['display_image'] = get_menu_image(menu)
    
    return render_template('customer/restaurant_detail.html',
                         restaurant=restaurant,
                         menus=menus)

@customer_bp.route('/cart')
@login_required
def cart():
    """Shopping cart"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for menu_id, quantity in cart.items():
        menu = Menu.find_by_id(menu_id)
        if menu:
            item_total = menu['price'] * quantity
            cart_items.append({
                'menu': menu,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('customer/cart.html',
                         cart_items=cart_items,
                         total=total)

@customer_bp.route('/cart/add-from-home', methods=['POST'])
def add_to_cart_from_home():
    """Add item to cart from home page - check login first"""
    # Kiểm tra đăng nhập
    if not session.get('user_id'):
        flash('Vui lòng đăng ký tài khoản để đặt món', 'info')
        return redirect(url_for('auth.register'))
    
    user = get_current_user()
    if not user or user.get('role') != 'customer':
        flash('Chỉ khách hàng mới có thể đặt món', 'warning')
        return redirect(url_for('main.index'))
    
    menu_id = request.form.get('menu_id')
    rest_id = request.form.get('rest_id')
    quantity = int(request.form.get('quantity', 1))
    
    if not menu_id:
        flash('Thiếu thông tin món ăn', 'danger')
        return redirect(url_for('main.index'))
    
    # Kiểm tra menu có tồn tại không
    menu = Menu.find_by_id(menu_id)
    if not menu:
        flash('Món ăn không tồn tại', 'danger')
        return redirect(url_for('main.index'))
    
    # Kiểm tra menu có thuộc nhà hàng đúng không
    if rest_id and str(menu.get('rest_id')) != str(rest_id):
        flash('Món ăn không thuộc nhà hàng này', 'danger')
        return redirect(url_for('main.index'))
    
    # Kiểm tra giỏ hàng hiện tại có món từ nhà hàng khác không
    if 'cart' in session and session['cart']:
        # Lấy rest_id của món đầu tiên trong giỏ hàng
        first_menu_id = list(session['cart'].keys())[0]
        first_menu = Menu.find_by_id(first_menu_id)
        if first_menu and str(first_menu.get('rest_id')) != str(menu.get('rest_id')):
            flash('Giỏ hàng của bạn đã có món từ nhà hàng khác. Vui lòng thanh toán hoặc xóa giỏ hàng trước khi thêm món mới.', 'warning')
            return redirect(url_for('customer.cart'))
    
    # Thêm vào giỏ hàng
    if 'cart' not in session:
        session['cart'] = {}
    
    current_qty = session['cart'].get(menu_id, 0)
    session['cart'][menu_id] = current_qty + quantity
    session.modified = True
    
    # Lưu cart vào database
    User.save_cart(str(user['_id']), session['cart'])
    
    flash('Đã thêm món vào giỏ hàng!', 'success')
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add item to cart"""
    menu_id = request.form.get('menu_id')
    quantity = int(request.form.get('quantity', 1))
    user = get_current_user()
    rest_id = request.form.get('rest_id')  # Optional, for validation
    
    if not menu_id:
        flash('Thiếu thông tin món ăn', 'danger')
        if rest_id:
            return redirect(url_for('customer.restaurant_detail', rest_id=rest_id))
        return redirect(url_for('customer.restaurants'))
    
    # Kiểm tra menu có tồn tại không
    menu = Menu.find_by_id(menu_id)
    if not menu:
        flash('Món ăn không tồn tại', 'danger')
        if rest_id:
            return redirect(url_for('customer.restaurant_detail', rest_id=rest_id))
        return redirect(url_for('customer.restaurants'))
    
    # Kiểm tra giỏ hàng hiện tại có món từ nhà hàng khác không
    if 'cart' in session and session['cart']:
        # Lấy rest_id của món đầu tiên trong giỏ hàng
        first_menu_id = list(session['cart'].keys())[0]
        first_menu = Menu.find_by_id(first_menu_id)
        if first_menu and str(first_menu.get('rest_id')) != str(menu.get('rest_id')):
            flash('Giỏ hàng của bạn đã có món từ nhà hàng khác. Vui lòng thanh toán hoặc xóa giỏ hàng trước khi thêm món mới.', 'warning')
            return redirect(url_for('customer.cart'))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    current_qty = session['cart'].get(menu_id, 0)
    session['cart'][menu_id] = current_qty + quantity
    session.modified = True
    
    # Lưu cart vào database
    User.save_cart(str(user['_id']), session['cart'])
    
    flash('Đã thêm món vào giỏ hàng!', 'success')
    
    # Nếu có rest_id, quay lại trang nhà hàng, nếu không thì vào giỏ hàng
    if rest_id:
        return redirect(url_for('customer.restaurant_detail', rest_id=rest_id))
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/update-quantity', methods=['POST'])
@login_required
def update_cart_quantity():
    """Update item quantity in cart"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Phiên đăng nhập đã hết hạn'}), 401
    
    data = request.get_json()
    menu_id = data.get('menu_id')
    quantity = int(data.get('quantity', 1))
    
    if not menu_id:
        return jsonify({'success': False, 'message': 'Thiếu thông tin món ăn'}), 400
    
    # Validate quantity
    if quantity < 1:
        quantity = 1
    if quantity > 99:
        quantity = 99
    
    # Kiểm tra menu có tồn tại không
    menu = Menu.find_by_id(menu_id)
    if not menu:
        return jsonify({'success': False, 'message': 'Món ăn không tồn tại'}), 404
    
    # Cập nhật số lượng trong session
    if 'cart' not in session:
        session['cart'] = {}
    
    if menu_id in session['cart']:
        session['cart'][menu_id] = quantity
        session.modified = True
        
        # Lưu cart vào database
        User.save_cart(str(user['_id']), session['cart'])
        
        return jsonify({'success': True, 'message': 'Đã cập nhật số lượng'})
    else:
        return jsonify({'success': False, 'message': 'Món ăn không có trong giỏ hàng'}), 404

@customer_bp.route('/cart/remove/<menu_id>', methods=['POST'])
@login_required
def remove_from_cart(menu_id):
    """Remove item from cart"""
    user = get_current_user()
    
    if 'cart' in session and menu_id in session['cart']:
        del session['cart'][menu_id]
        session.modified = True
        
        # Lưu cart vào database
        User.save_cart(str(user['_id']), session['cart'])
    
    return redirect(url_for('customer.cart'))

@customer_bp.route('/orders')
@login_required
def orders():
    """Customer orders list"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    orders_list = Order.find_by_user(str(user['_id']))
    
    return render_template('customer/orders.html', orders=orders_list)

@customer_bp.route('/reviews')
@login_required
def reviews():
    """Customer reviews list - Lịch sử đánh giá của khách hàng"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    # Lấy tất cả reviews của khách hàng này
    reviews_list = list(get_db().reviews.find({"user_id": ObjectId(user['_id'])}).sort("created_at", -1))
    
    # Lấy thông tin nhà hàng và shipper cho mỗi review
    for review in reviews_list:
        if review.get('restaurant_id'):
            review['restaurant'] = Restaurant.find_by_id(str(review['restaurant_id']))
        if review.get('shipper_id'):
            review['shipper'] = User.find_by_id(str(review['shipper_id']))
        if review.get('order_id'):
            review['order'] = Order.find_by_id(str(review['order_id']))
    
    return render_template('customer/reviews.html', reviews=reviews_list)

@customer_bp.route('/restaurant/<rest_id>/review', methods=['POST'])
@login_required
def review_restaurant(rest_id):
    """Đánh giá nhà hàng (không cần order_id)"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    restaurant = Restaurant.find_by_id(rest_id)
    if not restaurant:
        flash('Nhà hàng không tồn tại', 'danger')
        return redirect(url_for('customer.restaurants'))
    
    # Lấy dữ liệu từ form
    rating = int(request.form.get('rating', 0))
    comment = request.form.get('comment', '').strip()
    
    if rating < 1 or rating > 5:
        flash('Vui lòng chọn đánh giá từ 1 đến 5 sao', 'warning')
        return redirect(url_for('customer.restaurants'))
    
    # Xử lý upload ảnh
    image_urls = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = save_review_image(file, str(user['_id']))
                    if filename:
                        image_urls.append(url_for('static', filename=f'uploads/reviews/{filename}'))
    
    # Tạo review data (không có order_id)
    review_data = {
        'user_id': str(user['_id']),
        'restaurant_id': rest_id,
        'restaurant_rating': rating,
        'restaurant_comment': comment if comment else None,
        'images': image_urls if image_urls else [],
        'created_at': datetime.now()
    }
    
    # Kiểm tra xem đã có review cho nhà hàng này chưa (không có order_id)
    # Nếu có thì update, nếu không thì tạo mới
    existing_review = get_db().reviews.find_one({
        'user_id': ObjectId(user['_id']),
        'restaurant_id': ObjectId(rest_id),
        'order_id': {'$exists': False}  # Review không có order_id
    })
    
    if existing_review:
        # Update review cũ
        get_db().reviews.update_one(
            {'_id': existing_review['_id']},
            {'$set': {
                'restaurant_rating': rating,
                'restaurant_comment': comment if comment else None,
                'images': image_urls if image_urls else [],
                'created_at': datetime.now()
            }}
        )
        flash('Đã cập nhật đánh giá của bạn', 'success')
    else:
        # Tạo review mới
        Review.create(review_data)
        flash('Cảm ơn bạn đã đánh giá nhà hàng!', 'success')
    
    # Cập nhật rating trung bình của nhà hàng
    avg_rating = Review.calculate_restaurant_rating(rest_id)
    Restaurant.update(rest_id, {'rating': avg_rating})
    
    return redirect(url_for('customer.restaurants'))

@customer_bp.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """Order detail"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    order = Order.find_by_id(order_id)
    
    if not order or str(order['user_id']) != str(user['_id']):
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('customer.orders'))
    
    restaurant = Restaurant.find_by_id(str(order['rest_id']))
    payment = Payment.find_by_order(order_id)
    
    # Kiểm tra đã đánh giá chưa
    review = Review.find_by_order(order_id)
    
    # Lấy thông tin shipper nếu có
    shipper = None
    if order.get('shipper_id'):
        shipper = User.find_by_id(str(order['shipper_id']))
    
    # Lấy thông tin menu items từ order để hiển thị form đánh giá món ăn
    menu_items = []
    if order.get('items'):
        items = order.get('items', [])
        if isinstance(items, list) and len(items) > 0:
            # Format mới: array of objects
            if isinstance(items[0], dict):
                for item in items:
                    menu_id = item.get('menu_id') or item.get('_id')
                    if menu_id:
                        menu = Menu.find_by_id(str(menu_id))
                        if menu:
                            menu_items.append({
                                'menu': menu,
                                'quantity': item.get('quantity', 1)
                            })
            # Format cũ: array of strings (tên món)
            elif isinstance(items[0], str):
                # Tìm menu theo tên trong restaurant
                for item_name in items:
                    menu = get_db().menus.find_one({
                        'rest_id': ObjectId(order['rest_id']),
                        'name': item_name
                    })
                    if menu:
                        menu_items.append({
                            'menu': menu,
                            'quantity': 1
                        })
    
    return render_template('customer/order_detail.html',
                         order=order,
                         restaurant=restaurant,
                         payment=payment,
                         shipper=shipper,
                         review=review,
                         menu_items=menu_items)

@customer_bp.route('/order/<order_id>/confirm-received', methods=['POST'])
@login_required
def confirm_received(order_id):
    """Khách hàng xác nhận đã nhận hàng"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    # Xác nhận nhận hàng
    result = Order.confirm_received(order_id, str(user['_id']))
    
    if result and result.modified_count > 0:
        # Cập nhật tiền ship cho shipper khi khách hàng xác nhận nhận hàng
        from app.utils.revenue import update_shipper_delivery_fee
        update_shipper_delivery_fee(order_id)
        
        flash('Cảm ơn bạn đã xác nhận nhận hàng! Bây giờ bạn có thể đánh giá đơn hàng.', 'success')
    else:
        flash('Không thể xác nhận nhận hàng. Vui lòng kiểm tra lại trạng thái đơn hàng.', 'danger')
    
    return redirect(url_for('customer.order_detail', order_id=order_id))

@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout and create order"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        cart = session.get('cart', {})
        
        if not cart:
            flash('Giỏ hàng trống', 'warning')
            return redirect(url_for('customer.cart'))
        
        # Get order data
        rest_id = request.form.get('rest_id')
        delivery_address = request.form.get('delivery_address')
        payment_method = request.form.get('payment_method')
        promotion_code = request.form.get('promotion_code', '')
        
        if not all([rest_id, delivery_address, payment_method]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return redirect(url_for('customer.cart'))
        
        # Build order items
        items = []
        total = 0
        for menu_id, quantity in cart.items():
            menu = Menu.find_by_id(menu_id)
            if menu:
                item_total = menu['price'] * quantity
                items.append({
                    'menu_id': menu_id,
                    'name': menu['name'],
                    'quantity': quantity,
                    'price': menu['price']
                })
                total += item_total
        
        delivery_fee = 15000  # Fixed delivery fee
        
        # Create order
        order_data = {
            'user_id': str(user['_id']),
            'rest_id': rest_id,
            'items': items,
            'total': total + delivery_fee,
            'delivery_fee': delivery_fee,
            'delivery_address': delivery_address,
            'promotion_code': promotion_code if promotion_code else None,
            'status': 'pending',
            'shipper_id': None
        }
        
        order_id = Order.create(order_data)
        order_id_str = str(order_id)  # Convert ObjectId to string ngay từ đầu
        
        # Create payment
        payment_data = {
            'order_id': order_id_str,
            'method': payment_method,
            'amount': total + delivery_fee,
            'status': 'pending' if payment_method != 'cash' else 'success',
            'paid_at': None
        }
        
        if payment_method == 'cash':
            payment_data['paid_at'] = datetime.now()
            Payment.create(payment_data)
            
            # Tính và cập nhật doanh thu cho admin (5%) và restaurant (95%)
            from app.utils.revenue import calculate_and_update_revenue
            calculate_and_update_revenue(order_id_str)
            
            # Clear cart (cả session và database)
            user = get_current_user()
            session['cart'] = {}
            session.modified = True
            User.save_cart(str(user['_id']), {})
            flash('Đặt hàng thành công!', 'success')
            return redirect(url_for('customer.order_detail', order_id=order_id_str))
        
        elif payment_method == 'vnpay':
            try:
                # Tạo payment record trước
                payment_id = Payment.create(payment_data)
                
                # Kiểm tra xem có cấu hình VnPay chưa
                from flask import current_app
                tmn_code = current_app.config.get('VNPAY_TMN_CODE', '')
                hash_secret = current_app.config.get('VNPAY_HASH_SECRET', '')
                
                # Kiểm tra cấu hình VnPay
                if not tmn_code or tmn_code == 'YOUR_TMN_CODE' or not hash_secret or hash_secret == 'YOUR_HASH_SECRET':
                    flash('VnPay chưa được cấu hình. Vui lòng cấu hình VNPAY_TMN_CODE và VNPAY_HASH_SECRET trong app/config.py', 'danger')
                    return redirect(url_for('customer.checkout'))
                
                # Sử dụng VnPay thật
                vnpay = VnPay()
                # Tạo order_info ngắn gọn, không có ký tự đặc biệt
                order_info = f"Don hang {order_id_str[:8]}"
                
                # Lưu mapping order_id -> TxnRef sẽ được tạo (để tìm lại order sau)
                # Tạo TxnRef trước để lưu vào payment
                import time
                timestamp = int(time.time() * 1000) % 100000000
                order_id_clean = str(order_id_str).replace('-', '').replace('ObjectId', '')[:20]
                txn_ref = f"{timestamp}{order_id_clean}"[:36]
                
                # Lưu TxnRef vào payment để có thể tìm lại order
                get_db().payments.update_one(
                    {'_id': payment_id},
                    {'$set': {'txn_ref': txn_ref}}
                )
                
                try:
                    payment_url = vnpay.create_payment_url(
                        order_id=order_id_str,
                        amount=total + delivery_fee,
                        order_info=order_info
                    )
                except Exception as e:
                    flash(f'Lỗi khi tạo URL thanh toán: {str(e)}', 'danger')
                    return redirect(url_for('customer.checkout'))
                
                # Lưu order_id vào session để xử lý sau khi thanh toán
                session['pending_order_id'] = order_id_str
                session.modified = True
                
                # Redirect đến payment gateway
                return redirect(payment_url)
            except ValueError as e:
                flash(f'Lỗi cấu hình VnPay: {str(e)}', 'danger')
                return redirect(url_for('customer.checkout'))
            except Exception as e:
                flash(f'Lỗi khi tạo thanh toán: {str(e)}', 'danger')
                return redirect(url_for('customer.checkout'))
        
        # Đã bỏ phần thanh toán bằng thẻ tín dụng/ghi nợ
        # elif payment_method == 'card':
        #     # Tạo payment record
        #     Payment.create(payment_data)
        #     # Clear cart (cả session và database)
        #     user = get_current_user()
        #     session['cart'] = {}
        #     session.modified = True
        #     User.save_cart(str(user['_id']), {})
        #     flash('Đặt hàng thành công! Thanh toán bằng thẻ sẽ được xử lý sau.', 'success')
        #     return redirect(url_for('customer.order_detail', order_id=order_id_str))
        
        else:
            flash('Phương thức thanh toán không hợp lệ', 'danger')
            return redirect(url_for('customer.checkout'))
    
    # GET request - show checkout form
    cart = session.get('cart', {})
    if not cart:
        flash('Giỏ hàng trống', 'warning')
        return redirect(url_for('customer.cart'))
    
    # Get restaurant from first item
    first_menu_id = list(cart.keys())[0]
    first_menu = Menu.find_by_id(first_menu_id)
    restaurant = Restaurant.find_by_id(str(first_menu['rest_id'])) if first_menu else None
    
    # Build cart items for display
    cart_items = []
    subtotal = 0
    for menu_id, quantity in cart.items():
        menu = Menu.find_by_id(menu_id)
        if menu:
            item_total = menu['price'] * quantity
            cart_items.append({
                'menu': menu,
                'quantity': quantity,
                'total': item_total
            })
            subtotal += item_total
    
    delivery_fee = 15000
    total = subtotal + delivery_fee
    
    return render_template('customer/checkout.html', 
                         restaurant=restaurant,
                         cart_items=cart_items,
                         subtotal=subtotal,
                         delivery_fee=delivery_fee,
                         total=total)

@customer_bp.route('/payment/vnpay_return')
@login_required
def vnpay_return():
    """Xử lý callback từ VnPay sau khi thanh toán"""
    vnpay = VnPay()
    
    # Lấy dữ liệu từ VnPay
    vnpay_data = request.args.to_dict()
    
    # Debug: Log dữ liệu nhận được (chỉ trong development)
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug(f"VnPay return data: {vnpay_data}")
    
    # Xác thực thanh toán
    result = vnpay.verify_payment(vnpay_data)
    
    if result['success']:
        # Thanh toán thành công
        # Tìm order_id từ session (cách đơn giản nhất)
        order_id = None
        
        # Cách 1: Tìm từ session
        if 'pending_order_id' in session:
            order_id = session.get('pending_order_id')
        
        # Cách 2: Nếu không có trong session, thử tìm từ TxnRef
        if not order_id:
            txn_ref = result.get('txn_ref') or result.get('order_id')
            if txn_ref:
                # Tìm payment với txn_ref
                payment = get_db().payments.find_one({'txn_ref': txn_ref})
                if payment:
                    order_id = str(payment['order_id'])
        
        if not order_id:
            flash('Không tìm thấy đơn hàng', 'danger')
            return redirect(url_for('customer.orders'))
        
        order = Order.find_by_id(order_id)
        
        if order:
            # Cập nhật payment
            payment = Payment.find_by_order(order_id)
            if payment:
                # Cập nhật payment status và thông tin
                get_db().payments.update_one(
                    {'_id': payment['_id']},
                    {'$set': {
                        'status': 'success',
                        'paid_at': datetime.now(),
                        'transaction_id': result.get('transaction_id'),
                        'bank_code': result.get('bank_code'),
                        'updated_at': datetime.now()
                    }}
                )
                
                # Tính và cập nhật doanh thu cho admin (5%) và restaurant (95%)
                from app.utils.revenue import calculate_and_update_revenue
                calculate_and_update_revenue(order_id)
            
            # Clear pending order from session
            if 'pending_order_id' in session:
                del session['pending_order_id']
                session.modified = True
            
            # Clear cart (cả session và database)
            user = get_current_user()
            if user:
                session['cart'] = {}
                session.modified = True
                User.save_cart(str(user['_id']), {})
            else:
                # Nếu session bị mất, chỉ clear session cart
                session['cart'] = {}
                session.modified = True
            
            flash('Thanh toán thành công!', 'success')
            return redirect(url_for('customer.order_detail', order_id=order_id))
        else:
            flash('Không tìm thấy đơn hàng', 'danger')
            return redirect(url_for('customer.orders'))
    else:
        # Thanh toán thất bại
        order_id = result.get('order_id')
        if order_id:
            # Cập nhật payment status
            payment = Payment.find_by_order(order_id)
            if payment:
                get_db().payments.update_one(
                    {'_id': payment['_id']},
                    {'$set': {
                        'status': 'failed',
                        'updated_at': datetime.now()
                    }}
                )
        
        flash(f'Thanh toán thất bại: {result.get("message", "Lỗi không xác định")}', 'danger')
        return redirect(url_for('customer.orders'))

@customer_bp.route('/payment/vnpay_ipn', methods=['POST', 'GET'])
def vnpay_ipn():
    """
    IPN URL - VnPay gửi thông báo kết quả thanh toán
    Theo tài liệu: https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
    IPN URL được gọi bởi VnPay server, không cần authentication
    """
    vnpay = VnPay()
    
    # Lấy dữ liệu từ VnPay (có thể là POST hoặc GET)
    if request.method == 'POST':
        vnpay_data = request.form.to_dict()
    else:
        vnpay_data = request.args.to_dict()
    
    # Xác thực thanh toán
    result = vnpay.verify_payment(vnpay_data)
    
    if result['success']:
        # Thanh toán thành công - cập nhật payment
        order_id = result['order_id']
        payment = Payment.find_by_order(order_id)
        
        if payment:
            # Kiểm tra xem đã cập nhật chưa (tránh duplicate)
            if payment.get('status') != 'success':
                get_db().payments.update_one(
                    {'_id': payment['_id']},
                    {'$set': {
                        'status': 'success',
                        'paid_at': datetime.now(),
                        'transaction_id': result.get('transaction_id'),
                        'bank_code': result.get('bank_code'),
                        'updated_at': datetime.now()
                    }}
                )
                
                # Tính và cập nhật doanh thu cho admin (5%) và restaurant (95%)
                from app.utils.revenue import calculate_and_update_revenue
                calculate_and_update_revenue(order_id)
        
        # Trả về response cho VnPay (theo tài liệu)
        return jsonify({'RspCode': '00', 'Message': 'Success'}), 200
    else:
        # Thanh toán thất bại
        order_id = result.get('order_id')
        if order_id:
            payment = Payment.find_by_order(order_id)
            if payment and payment.get('status') != 'failed':
                get_db().payments.update_one(
                    {'_id': payment['_id']},
                    {'$set': {
                        'status': 'failed',
                        'updated_at': datetime.now()
                    }}
                )
        
        # Trả về response cho VnPay
        return jsonify({'RspCode': '00', 'Message': 'Confirm'}), 200

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})

def save_review_image(file, user_id):
    """Save a single review image and return filename"""
    if file and file.filename:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        review_folder = os.path.join(upload_folder, 'reviews')
        os.makedirs(review_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = f"{timestamp}{user_id}_{filename}"
        
        filepath = os.path.join(review_folder, filename)
        file.save(filepath)
        return filename
    return None

def save_review_images(files):
    """Save uploaded review images and return URLs"""
    image_urls = []
    if files:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        review_folder = os.path.join(upload_folder, 'reviews')
        os.makedirs(review_folder, exist_ok=True)
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                
                filepath = os.path.join(review_folder, filename)
                file.save(filepath)
                
                image_url = flask_url_for('static', filename=f'uploads/reviews/{filename}')
                image_urls.append(image_url)
    
    return image_urls

@customer_bp.route('/order/<order_id>/review', methods=['POST'])
@login_required
def create_review(order_id):
    """Tạo đánh giá cho đơn hàng (nhà hàng, shipper và món ăn)"""
    user = get_current_user()
    if not user:
        flash('Phiên đăng nhập đã hết hạn', 'warning')
        return redirect(url_for('auth.login'))
    
    order = Order.find_by_id(order_id)
    if not order or str(order['user_id']) != str(user['_id']):
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('customer.orders'))
    
    # Chỉ cho phép đánh giá khi đơn hàng đã completed (khách đã xác nhận nhận hàng)
    if order.get('status') != 'completed':
        flash('Chỉ có thể đánh giá sau khi bạn đã xác nhận nhận hàng', 'warning')
        return redirect(url_for('customer.order_detail', order_id=order_id))
    
    # Kiểm tra đã đánh giá chưa
    existing_review = Review.find_by_order(order_id)
    if existing_review:
        flash('Bạn đã đánh giá đơn hàng này rồi', 'info')
        return redirect(url_for('customer.order_detail', order_id=order_id))
    
    # Lấy dữ liệu từ form
    restaurant_rating = request.form.get('restaurant_rating', type=int)
    restaurant_comment = request.form.get('restaurant_comment', '')
    driver_rating = request.form.get('driver_rating', type=int) if order.get('shipper_id') else None
    driver_comment = request.form.get('driver_comment', '') if order.get('shipper_id') else ''
    
    # Validate ratings (chỉ cho phép 1-5 sao, không cho 0 sao)
    if not restaurant_rating or restaurant_rating < 1 or restaurant_rating > 5:
        flash('Vui lòng chọn số sao nhà hàng từ 1 đến 5', 'danger')
        return redirect(url_for('customer.order_detail', order_id=order_id))
    
    if order.get('shipper_id') and (driver_rating is None or driver_rating < 1 or driver_rating > 5):
        flash('Vui lòng chọn số sao tài xế từ 1 đến 5', 'danger')
        return redirect(url_for('customer.order_detail', order_id=order_id))
    
    # Xử lý upload ảnh
    uploaded_files = request.files.getlist('review_images')
    image_urls = save_review_images(uploaded_files)
    
    # Lấy đánh giá món ăn
    menu_ratings = []
    if order.get('items'):
        items = order.get('items', [])
        if isinstance(items, list) and len(items) > 0:
            # Format mới: array of objects
            if isinstance(items[0], dict):
                for item in items:
                    menu_id = item.get('menu_id') or item.get('_id')
                    if menu_id:
                        menu_rating = request.form.get(f'menu_rating_{menu_id}', type=int)
                        menu_comment = request.form.get(f'menu_comment_{menu_id}', '')
                        # Chỉ thêm menu_rating nếu >= 1 (không cho 0 sao)
                        if menu_rating is not None and menu_rating >= 1:
                            menu = Menu.find_by_id(str(menu_id))
                            if menu:
                                menu_ratings.append({
                                    'menu_id': str(menu_id),
                                    'menu_name': menu.get('name', 'N/A'),
                                    'rating': menu_rating,
                                    'comment': menu_comment
                                })
            # Format cũ: array of strings - tìm menu theo tên
            elif isinstance(items[0], str):
                for item_name in items:
                    menu = get_db().menus.find_one({
                        'rest_id': ObjectId(order['rest_id']),
                        'name': item_name
                    })
                    if menu:
                        menu_id = str(menu['_id'])
                        menu_rating = request.form.get(f'menu_rating_{menu_id}', type=int)
                        menu_comment = request.form.get(f'menu_comment_{menu_id}', '')
                        if menu_rating is not None:
                            menu_ratings.append({
                                'menu_id': menu_id,
                                'menu_name': menu.get('name', 'N/A'),
                                'rating': menu_rating,
                                'comment': menu_comment
                            })
    
    # Tạo review
    review_data = {
        'order_id': order_id,
        'user_id': str(user['_id']),
        'restaurant_id': str(order['rest_id']),
        'restaurant_rating': restaurant_rating,
        'restaurant_comment': restaurant_comment,
        'menu_ratings': menu_ratings,
        'images': image_urls
    }
    
    if order.get('shipper_id'):
        review_data['shipper_id'] = str(order['shipper_id'])
        review_data['driver_rating'] = driver_rating
        review_data['driver_comment'] = driver_comment
    
    Review.create(review_data)
    
    # Cập nhật rating của nhà hàng
    new_rating = Review.calculate_restaurant_rating(str(order['rest_id']))
    Restaurant.update(str(order['rest_id']), {'rating': new_rating})
    
    # Cập nhật rating của shipper
    if order.get('shipper_id'):
        shipper_id = str(order['shipper_id'])
        new_shipper_rating = Review.calculate_shipper_rating(shipper_id)
        User.update(shipper_id, {'delivery_stats.avg_rating': new_shipper_rating})
    
    flash('Cảm ơn bạn đã đánh giá!', 'success')
    return redirect(url_for('customer.order_detail', order_id=order_id))

