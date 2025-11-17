# Import datetime để lấy thời gian hiện tại
from datetime import datetime
# Import ObjectId để chuyển đổi string ID sang ObjectId
from bson import ObjectId
# Import get_db để lấy database instance
from app.database import get_db
# Import User và Order models
from app.models import User, Order

def calculate_and_update_revenue(order_id):
    """
    Tính và cập nhật doanh thu cho admin (5%) và restaurant (95%) khi đơn hàng được thanh toán
    Chỉ tính trên tổng tiền món (không tính phí ship)
    Tham số: order_id (string) - ID của đơn hàng
    """
    order = Order.find_by_id(order_id)
    if not order:
        return False
    
    # Tính tổng tiền món (không tính phí ship)
    delivery_fee = order.get('delivery_fee', 15000)
    total_amount = order.get('total', 0)
    subtotal = total_amount - delivery_fee  # Tổng tiền món
    
    # Tính doanh thu
    admin_revenue = subtotal * 0.05  # Admin: 5%
    restaurant_revenue = subtotal * 0.95  # Restaurant: 95%
    
    # Lấy restaurant owner
    rest_id = order.get('rest_id')
    restaurant = get_db().restaurants.find_one({'_id': ObjectId(rest_id)}) if rest_id else None
    restaurant_owner_id = restaurant.get('owner_id') if restaurant else None
    
    # Cập nhật doanh thu cho admin (tìm admin đầu tiên)
    admin = get_db().users.find_one({'role': 'admin'})
    if admin:
        current_admin_revenue = admin.get('revenue', 0)
        get_db().users.update_one(
            {'_id': admin['_id']},
            {'$set': {'revenue': current_admin_revenue + admin_revenue}}
        )
    
    # Cập nhật doanh thu cho restaurant owner
    if restaurant_owner_id:
        owner = User.find_by_id(str(restaurant_owner_id))
        if owner:
            current_owner_revenue = owner.get('revenue', 0)
            User.update(str(restaurant_owner_id), {
                'revenue': current_owner_revenue + restaurant_revenue
            })
    
    return True

def update_shipper_delivery_fee(order_id):
    """
    Cập nhật tiền ship và stats cho shipper khi khách hàng xác nhận nhận hàng (order status = completed)
    Tham số: order_id (string) - ID của đơn hàng
    """
    order = Order.find_by_id(order_id)
    if not order or order.get('status') != 'completed':
        return False
    
    shipper_id = order.get('shipper_id')
    if not shipper_id:
        return False
    
    # Lấy phí ship (mặc định 15000)
    delivery_fee = order.get('delivery_fee', 15000)
    
    # Lấy shipper
    shipper = User.find_by_id(str(shipper_id))
    if not shipper:
        return False
    
    # Cập nhật tiền ship cho shipper
    current_delivery_earnings = shipper.get('delivery_earnings', 0)
    
    # Cập nhật stats cho shipper (chỉ khi khách hàng xác nhận nhận hàng)
    stats = shipper.get('delivery_stats', {})
    stats['total_orders'] = stats.get('total_orders', 0) + 1
    stats['completed_orders'] = stats.get('completed_orders', 0) + 1
    
    # Cập nhật cả tiền ship và stats
    User.update(str(shipper_id), {
        'delivery_earnings': current_delivery_earnings + delivery_fee,
        'delivery_stats': stats
    })
    
    return True

def get_admin_revenue():
    """
    Lấy tổng doanh thu của admin
    Trả về: Số tiền doanh thu (float)
    """
    admin = get_db().users.find_one({'role': 'admin'})
    if admin:
        return admin.get('revenue', 0)
    return 0

def get_restaurant_owner_revenue(owner_id):
    """
    Lấy tổng doanh thu của chủ nhà hàng
    Tham số: owner_id (string) - ID của chủ nhà hàng
    Trả về: Số tiền doanh thu (float)
    """
    owner = User.find_by_id(owner_id)
    if owner:
        return owner.get('revenue', 0)
    return 0

def get_shipper_earnings(shipper_id):
    """
    Lấy tổng tiền ship của shipper
    Tham số: shipper_id (string) - ID của shipper
    Trả về: Số tiền ship (float)
    """
    shipper = User.find_by_id(shipper_id)
    if shipper:
        return shipper.get('delivery_earnings', 0)
    return 0

