from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import User, Restaurant, Order, Payment
from app.utils.auth import login_required, role_required, get_current_user
from app.utils.helpers import to_object_id, paginate
from app.database import get_db
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Admin dashboard with statistics"""
    db = get_db()
    
    # Lấy doanh thu của admin
    from app.utils.revenue import get_admin_revenue
    admin_revenue = get_admin_revenue()
    
    # Statistics
    stats = {
        'total_users': db.users.count_documents({}),
        'total_restaurants': db.restaurants.count_documents({}),
        'total_orders': db.orders.count_documents({}),
        'pending_orders': db.orders.count_documents({'status': 'pending'}),
        'pending_restaurants': db.restaurants.count_documents({'status': 'pending'}),
        'pending_shippers': db.users.count_documents({'role': 'shipper', 'status': 'pending'}),
        'pending_restaurant_owners': db.users.count_documents({'role': 'restaurant_owner', 'status': 'pending'}),
        'total_restaurant_owners': db.users.count_documents({'role': 'restaurant_owner'}),
        'revenue': admin_revenue
    }
    
    # Recent orders
    recent_orders = list(db.orders.find().sort('created_at', -1).limit(10))
    
    return render_template('admin/dashboard.html', stats=stats, orders=recent_orders)

@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    """Manage users"""
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = {}
    if role_filter:
        query['role'] = role_filter
    if status_filter:
        query['status'] = status_filter
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'phone': {'$regex': search, '$options': 'i'}}
        ]
    
    users_list = list(get_db().users.find(query))
    
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/user/<user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    """Toggle user status (active/banned)"""
    user = User.find_by_id(user_id)
    if not user:
        flash('Người dùng không tồn tại', 'danger')
        return redirect(url_for('admin.users'))
    
    new_status = 'banned' if user.get('status') == 'active' else 'active'
    User.update(user_id, {'status': new_status})
    
    flash(f'Đã {"khóa" if new_status == "banned" else "mở khóa"} tài khoản', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/restaurants')
@login_required
@role_required('admin')
def restaurants():
    """Manage restaurants"""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    if search:
        filters['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'addr': {'$regex': search, '$options': 'i'}}
        ]
    
    restaurants_list = Restaurant.find_all(filters)
    
    # Lấy thông tin chủ nhà hàng cho mỗi restaurant
    for restaurant in restaurants_list:
        if restaurant.get('owner_id'):
            owner = User.find_by_id(str(restaurant['owner_id']))
            restaurant['owner'] = owner
        else:
            restaurant['owner'] = None
    
    return render_template('admin/restaurants.html', restaurants=restaurants_list)

@admin_bp.route('/restaurant/<rest_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_restaurant(rest_id):
    """Approve restaurant"""
    get_db().restaurants.update_one(
        {'_id': to_object_id(rest_id)},
        {'$set': {'status': 'approved', 'updated_at': datetime.now()}}
    )
    flash('Đã duyệt nhà hàng', 'success')
    return redirect(url_for('admin.restaurants'))

@admin_bp.route('/restaurant/<rest_id>/ban', methods=['POST'])
@login_required
@role_required('admin')
def ban_restaurant(rest_id):
    """Ban restaurant"""
    get_db().restaurants.update_one(
        {'_id': to_object_id(rest_id)},
        {'$set': {'status': 'banned', 'updated_at': datetime.now()}}
    )
    flash('Đã khóa nhà hàng', 'success')
    return redirect(url_for('admin.restaurants'))

@admin_bp.route('/shippers')
@login_required
@role_required('admin')
def shippers():
    """Manage shippers"""
    status_filter = request.args.get('status', '')
    
    query = {'role': 'shipper'}
    if status_filter:
        query['status'] = status_filter
    
    shippers_list = list(get_db().users.find(query))
    
    return render_template('admin/shippers.html', shippers=shippers_list)

@admin_bp.route('/shipper/<shipper_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_shipper(shipper_id):
    """Approve shipper"""
    User.update(shipper_id, {'status': 'active'})
    flash('Đã duyệt tài xế', 'success')
    return redirect(url_for('admin.shippers'))

@admin_bp.route('/restaurant-owner/<user_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_restaurant_owner(user_id):
    """Approve restaurant owner"""
    user = User.find_by_id(user_id)
    if not user or user.get('role') != 'restaurant_owner':
        flash('Người dùng không hợp lệ', 'danger')
        return redirect(url_for('admin.users'))
    
    User.update(user_id, {'status': 'active'})
    flash('Đã duyệt tài khoản chủ nhà hàng', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/orders')
@login_required
@role_required('admin')
def orders():
    """Manage all orders"""
    status_filter = request.args.get('status', '')
    
    query = {}
    if status_filter:
        query['status'] = status_filter
    
    orders_list = list(get_db().orders.find(query).sort('created_at', -1))
    
    return render_template('admin/orders.html', orders=orders_list)

@admin_bp.route('/order/<order_id>')
@login_required
@role_required('admin')
def order_detail(order_id):
    """Order detail"""
    order = Order.find_by_id(order_id)
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('admin.orders'))
    
    restaurant = Restaurant.find_by_id(str(order['rest_id']))
    user = User.find_by_id(str(order['user_id']))
    payment = Payment.find_by_order(order_id)
    
    return render_template('admin/order_detail.html',
                         order=order,
                         restaurant=restaurant,
                         user=user,
                         payment=payment)

@admin_bp.route('/restaurant-owners')
@login_required
@role_required('admin')
def restaurant_owners():
    """View mapping between restaurant owners and restaurants"""
    owners = User.find_by_role('restaurant_owner')
    
    # Lấy thông tin nhà hàng cho mỗi owner
    owners_data = []
    for owner in owners:
        restaurants = Restaurant.find_by_owner(str(owner['_id']))
        owners_data.append({
            'owner': owner,
            'restaurants': restaurants,
            'restaurant_count': len(restaurants)
        })
    
    return render_template('admin/restaurant_owners.html', owners_data=owners_data)

