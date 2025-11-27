from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import Order, User, Restaurant, Review, Payment
from app.utils.auth import login_required, get_current_user
from app.utils.helpers import to_object_id
from app.database import get_db
from datetime import datetime
from bson import ObjectId

shipper_bp = Blueprint('shipper', __name__, url_prefix='/shipper')

@shipper_bp.route('/dashboard')
@login_required
def dashboard():
    """Shipper dashboard"""
    user = get_current_user()
    if not user or user.get('role') != 'shipper':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if approved (accept both 'approved' and 'active' as approved status)
    user_status = user.get('status', '')
    if user_status not in ['approved', 'active']:
        flash('Tài khoản của bạn đang chờ duyệt', 'warning')
        return render_template('shipper/pending.html', user=user)
    
    # Get available orders
    available_orders = Order.find_available()
    
    # Get my orders (all statuses for tab view)
    my_orders_all = list(get_db().orders.find({
        'shipper_id': to_object_id(str(user['_id']))
    }).sort('created_at', -1))
    
    # Get active orders (preparing and delivering) for main view
    my_orders = [o for o in my_orders_all if o.get('status') in ['preparing', 'delivering']]
    
    # Get statistics
    stats = user.get('delivery_stats', {})
    
    # Lấy tổng tiền ship của shipper
    from app.utils.revenue import get_shipper_earnings
    delivery_earnings = get_shipper_earnings(str(user['_id']))
    stats['delivery_earnings'] = delivery_earnings
    
    # Calculate stats
    from app.models import Review
    stats['total_orders'] = len(my_orders_all)
    stats['completed_orders'] = len([o for o in my_orders_all if o.get('status') in ['delivered', 'completed']])
    stats['avg_rating'] = Review.calculate_shipper_rating(str(user['_id']))
    
    return render_template('shipper/dashboard.html',
                         user=user,
                         available_orders=available_orders,
                         my_orders=my_orders_all,  # Pass all orders for tabs
                         stats=stats)

@shipper_bp.route('/order/<order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    """Accept an order"""
    user = get_current_user()
    if not user or user.get('role') != 'shipper':
        flash('Bạn không có quyền', 'danger')
        return redirect(url_for('shipper.dashboard'))
    
    user_status = user.get('status', '')
    if user_status not in ['approved', 'active']:
        flash('Tài khoản chưa được duyệt', 'warning')
        return redirect(url_for('shipper.dashboard'))
    
    order = Order.find_by_id(order_id)
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('shipper.dashboard'))
    
    if order.get('shipper_id'):
        flash('Đơn hàng đã được nhận bởi shipper khác', 'warning')
        return redirect(url_for('shipper.dashboard'))
    
    # Check if order is in preparing status (đã được chủ nhà hàng chấp nhận)
    if order.get('status') != 'preparing':
        flash('Đơn hàng chưa được chủ nhà hàng chấp nhận', 'warning')
        return redirect(url_for('shipper.dashboard'))
    
    # Accept order - chuyển sang delivering (shipper đang giao)
    Order.update_status(order_id, 'delivering', str(user['_id']))
    
    # Nếu thanh toán bằng tiền mặt, tính doanh thu cho chủ nhà hàng và admin khi shipper nhận đơn
    payment = get_db().payments.find_one({'order_id': ObjectId(order_id)})
    if payment and payment.get('method') == 'cash' and payment.get('status') == 'pending':
        # Cập nhật payment status thành success
        get_db().payments.update_one(
            {'_id': payment['_id']},
            {'$set': {'status': 'success', 'paid_at': datetime.now()}}
        )
        
        # Tính và cập nhật doanh thu
        from app.utils.revenue import calculate_and_update_revenue
        calculate_and_update_revenue(order_id)
    
    flash('Đã nhận đơn hàng thành công', 'success')
    return redirect(url_for('shipper.order_detail', order_id=order_id))

@shipper_bp.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    """Order detail for shipper"""
    user = get_current_user()
    order = Order.find_by_id(order_id)
    
    if not order:
        flash('Đơn hàng không tồn tại', 'danger')
        return redirect(url_for('shipper.dashboard'))
    
    # Check if this is shipper's order
    if str(order.get('shipper_id')) != str(user['_id']):
        flash('Đây không phải đơn hàng của bạn', 'warning')
        return redirect(url_for('shipper.dashboard'))
    
    restaurant = Restaurant.find_by_id(str(order['rest_id']))
    customer = User.find_by_id(str(order['user_id']))
    
    return render_template('shipper/order_detail.html',
                         order=order,
                         restaurant=restaurant,
                         customer=customer)

@shipper_bp.route('/order/<order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Update order status"""
    user = get_current_user()
    order = Order.find_by_id(order_id)
    
    if not order or str(order.get('shipper_id')) != str(user['_id']):
        flash('Không có quyền cập nhật đơn hàng này', 'danger')
        return redirect(url_for('shipper.dashboard'))
    
    new_status = request.form.get('status')
    
    # Chỉ cho phép chuyển từ delivering sang delivered
    if order.get('status') != 'delivering':
        flash('Chỉ có thể cập nhật trạng thái khi đang giao hàng', 'warning')
        return redirect(url_for('shipper.order_detail', order_id=order_id))
    
    if new_status != 'delivered':
        flash('Trạng thái không hợp lệ', 'danger')
        return redirect(url_for('shipper.order_detail', order_id=order_id))
    
    Order.update_status(order_id, new_status)
    
    # LƯU Ý: Không cập nhật stats ở đây
    # Stats và tiền ship chỉ được cập nhật khi khách hàng xác nhận nhận hàng (status = completed)
    # Xem logic trong app/routes/customer.py - confirm_received()
    
    flash('Đã cập nhật trạng thái đơn hàng', 'success')
    return redirect(url_for('shipper.order_detail', order_id=order_id))

@shipper_bp.route('/orders')
@login_required
def orders():
    """Shipper orders history"""
    user = get_current_user()
    
    orders_list = list(get_db().orders.find({
        'shipper_id': to_object_id(str(user['_id']))
    }).sort('created_at', -1))
    
    return render_template('shipper/orders.html', orders=orders_list)

@shipper_bp.route('/stats')
@login_required
def stats():
    """Shipper statistics"""
    user = get_current_user()
    stats = user.get('delivery_stats', {})
    
    return render_template('shipper/stats.html', stats=stats, user=user)

@shipper_bp.route('/reviews')
@login_required
def reviews():
    """Shipper reviews - Đánh giá của khách hàng về shipper"""
    user = get_current_user()
    if not user or user.get('role') != 'shipper':
        flash('Bạn không có quyền truy cập', 'danger')
        return redirect(url_for('main.index'))
    
    # Lấy tất cả reviews của shipper này
    reviews_list = Review.find_by_shipper(str(user['_id']))
    
    # Lấy thông tin khách hàng và nhà hàng cho mỗi review
    for review in reviews_list:
        if review.get('user_id'):
            review['customer'] = User.find_by_id(str(review['user_id']))
        if review.get('restaurant_id'):
            review['restaurant'] = Restaurant.find_by_id(str(review['restaurant_id']))
        if review.get('order_id'):
            review['order'] = Order.find_by_id(str(review['order_id']))
    
    # Tính toán thống kê
    total_reviews = len(reviews_list)
    if total_reviews > 0:
        total_rating = sum(r.get('driver_rating', 0) for r in reviews_list)
        avg_rating = round(total_rating / total_reviews, 1)
        zero_star_count = sum(1 for r in reviews_list if r.get('driver_rating') == 0)
    else:
        avg_rating = 0.0
        zero_star_count = 0
    
    stats = {
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'zero_star_count': zero_star_count
    }
    
    return render_template('shipper/reviews.html', reviews=reviews_list, stats=stats)

