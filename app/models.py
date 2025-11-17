# Import datetime để lấy thời gian hiện tại khi tạo/cập nhật dữ liệu
from datetime import datetime
# Import ObjectId từ bson để chuyển đổi string ID sang ObjectId của MongoDB
from bson import ObjectId
# Import hàm get_db để lấy database instance từ database.py
from app.database import get_db

class User:
    """Class User - Model quản lý người dùng (khách hàng, admin, shipper, chủ nhà hàng)"""
    
    @staticmethod
    def find_by_phone(phone):
        """
        Tìm người dùng theo số điện thoại
        Tham số: phone (string) - Số điện thoại cần tìm
        Trả về: Document của user nếu tìm thấy, None nếu không tìm thấy
        """
        # Tìm một document trong collection users có trường phone khớp với số điện thoại truyền vào
        return get_db().users.find_one({"phone": phone})
    
    @staticmethod
    def find_by_id(user_id):
        """
        Tìm người dùng theo ID
        Tham số: user_id (string) - ID của user cần tìm
        Trả về: Document của user nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển user_id từ string sang ObjectId và tìm user có _id khớp
        return get_db().users.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def create(data):
        """
        Tạo người dùng mới
        Tham số: data (dict) - Dictionary chứa thông tin user (phone, name, password, role, v.v.)
        Trả về: ID của user vừa được tạo
        """
        # Thêm thời gian tạo vào dữ liệu user
        data['created_at'] = datetime.now()
        # Chèn document mới vào collection users và lưu kết quả
        result = get_db().users.insert_one(data)
        # Trả về ID của document vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def update(user_id, data):
        """
        Cập nhật thông tin người dùng
        Tham số: 
            user_id (string) - ID của user cần cập nhật
            data (dict) - Dictionary chứa các trường cần cập nhật
        Trả về: Kết quả của thao tác update
        """
        # Thêm thời gian cập nhật vào dữ liệu
        data['updated_at'] = datetime.now()
        # Cập nhật document có _id khớp với user_id, chỉ cập nhật các trường trong data
        return get_db().users.update_one(
            {"_id": ObjectId(user_id)},  # Điều kiện tìm: _id khớp với user_id
            {"$set": data}  # Toán tử $set để cập nhật các trường trong data
        )
    
    @staticmethod
    def find_by_role(role):
        """
        Tìm tất cả người dùng theo vai trò (role)
        Tham số: role (string) - Vai trò cần tìm (customer, admin, shipper, restaurant_owner)
        Trả về: List các document user có role khớp
        """
        # Tìm tất cả user có role khớp và chuyển kết quả thành list
        return list(get_db().users.find({"role": role}))
    
    @staticmethod
    def save_cart(user_id, cart):
        """
        Lưu giỏ hàng của người dùng vào database
        Tham số:
            user_id (string) - ID của user
            cart (dict) - Dictionary chứa thông tin giỏ hàng (menu_id: quantity)
        Trả về: Kết quả của thao tác update
        """
        # Cập nhật trường cart và cart_updated_at của user trong database
        return get_db().users.update_one(
            {"_id": ObjectId(user_id)},  # Tìm user theo ID
            {"$set": {"cart": cart, "cart_updated_at": datetime.now()}}  # Cập nhật giỏ hàng và thời gian
        )
    
    @staticmethod
    def get_cart(user_id):
        """
        Lấy giỏ hàng của người dùng từ database
        Tham số: user_id (string) - ID của user
        Trả về: Dictionary chứa giỏ hàng, hoặc {} nếu không tìm thấy user hoặc không có giỏ hàng
        """
        # Tìm user theo ID
        user = get_db().users.find_one({"_id": ObjectId(user_id)})
        # Nếu tìm thấy user và có trường cart thì trả về cart, ngược lại trả về dictionary rỗng
        return user.get('cart', {}) if user else {}

class Restaurant:
    """Class Restaurant - Model quản lý nhà hàng"""
    
    @staticmethod
    def find_all(filters=None, limit=None, skip=0):
        """
        Tìm tất cả nhà hàng với các điều kiện lọc, phân trang
        Tham số:
            filters (dict, optional) - Điều kiện lọc (ví dụ: {"status": "approved"})
            limit (int, optional) - Số lượng kết quả tối đa
            skip (int) - Số lượng document bỏ qua (dùng cho phân trang)
        Trả về: List các document restaurant
        """
        # Nếu không có filters thì dùng dictionary rỗng (tìm tất cả)
        query = filters or {}
        # Tìm các restaurant theo query, bỏ qua skip document đầu tiên
        cursor = get_db().restaurants.find(query).skip(skip)
        # Nếu có giới hạn số lượng thì áp dụng limit
        if limit:
            cursor = cursor.limit(limit)
        # Chuyển cursor thành list và trả về
        return list(cursor)
    
    @staticmethod
    def find_by_id(rest_id):
        """
        Tìm nhà hàng theo ID
        Tham số: rest_id (string) - ID của restaurant cần tìm
        Trả về: Document của restaurant nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển rest_id từ string sang ObjectId và tìm restaurant có _id khớp
        return get_db().restaurants.find_one({"_id": ObjectId(rest_id)})
    
    @staticmethod
    def find_by_owner(owner_id):
        """
        Tìm tất cả nhà hàng của một chủ sở hữu
        Tham số: owner_id (string) - ID của chủ nhà hàng
        Trả về: List các document restaurant thuộc về owner_id đó
        """
        # Tìm tất cả restaurant có owner_id khớp và chuyển thành list
        return list(get_db().restaurants.find({"owner_id": ObjectId(owner_id)}))
    
    @staticmethod
    def find_nearby(lat, lng, max_distance=5000):
        """
        Tìm nhà hàng gần một vị trí địa lý (sử dụng geospatial query)
        Tham số:
            lat (float) - Vĩ độ (latitude)
            lng (float) - Kinh độ (longitude)
            max_distance (int) - Khoảng cách tối đa tính bằng mét (mặc định 5000m = 5km)
        Trả về: List các restaurant trong bán kính max_distance từ vị trí (lat, lng)
        """
        # Sử dụng $near operator để tìm nhà hàng gần vị trí
        return list(get_db().restaurants.find({
            "loc": {  # Trường loc chứa tọa độ địa lý (GeoJSON Point)
                "$near": {  # Toán tử tìm kiếm gần
                    "$geometry": {
                        "type": "Point",  # Kiểu GeoJSON là Point
                        "coordinates": [lng, lat]  # Tọa độ [kinh độ, vĩ độ] - lưu ý thứ tự
                    },
                    "$maxDistance": max_distance  # Khoảng cách tối đa (mét)
                }
            },
            "status": "approved"  # Chỉ lấy nhà hàng đã được duyệt
        }))
    
    @staticmethod
    def create(data):
        """
        Tạo nhà hàng mới
        Tham số: data (dict) - Dictionary chứa thông tin restaurant (name, address, loc, owner_id, v.v.)
        Trả về: ID của restaurant vừa được tạo
        """
        # Thêm thời gian tạo vào dữ liệu
        data['created_at'] = datetime.now()
        # Nếu có owner_id trong data và không rỗng thì chuyển sang ObjectId
        if 'owner_id' in data and data['owner_id']:
            data['owner_id'] = ObjectId(data['owner_id'])
        # Chèn document mới vào collection restaurants
        result = get_db().restaurants.insert_one(data)
        # Trả về ID của restaurant vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def update(rest_id, data):
        """
        Cập nhật thông tin nhà hàng
        Tham số:
            rest_id (string) - ID của restaurant cần cập nhật
            data (dict) - Dictionary chứa các trường cần cập nhật
        Trả về: Kết quả của thao tác update
        """
        # Thêm thời gian cập nhật vào dữ liệu
        data['updated_at'] = datetime.now()
        # Nếu có owner_id trong data và không rỗng thì chuyển sang ObjectId
        if 'owner_id' in data and data['owner_id']:
            data['owner_id'] = ObjectId(data['owner_id'])
        # Cập nhật document có _id khớp với rest_id
        return get_db().restaurants.update_one(
            {"_id": ObjectId(rest_id)},  # Điều kiện tìm
            {"$set": data}  # Cập nhật các trường trong data
        )

class Menu:
    """Class Menu - Model quản lý món ăn/thực đơn của nhà hàng"""
    
    @staticmethod
    def find_by_restaurant(rest_id, filters=None):
        """
        Tìm tất cả món ăn của một nhà hàng
        Tham số:
            rest_id (string) - ID của restaurant
            filters (dict, optional) - Điều kiện lọc thêm (ví dụ: {"status": "available"})
        Trả về: List các document menu thuộc về restaurant đó
        """
        # Tạo query cơ bản: tìm menu có rest_id khớp
        query = {"rest_id": ObjectId(rest_id)}
        # Nếu có filters thì thêm vào query
        if filters:
            query.update(filters)
        # Tìm tất cả menu theo query và chuyển thành list
        return list(get_db().menus.find(query))
    
    @staticmethod
    def find_by_id(menu_id):
        """
        Tìm món ăn theo ID
        Tham số: menu_id (string) - ID của menu cần tìm
        Trả về: Document của menu nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển menu_id từ string sang ObjectId và tìm menu có _id khớp
        return get_db().menus.find_one({"_id": ObjectId(menu_id)})
    
    @staticmethod
    def create(data):
        """
        Tạo món ăn mới
        Tham số: data (dict) - Dictionary chứa thông tin menu (name, price, description, rest_id, v.v.)
        Trả về: ID của menu vừa được tạo
        """
        # Chuyển rest_id từ string sang ObjectId (ID của nhà hàng sở hữu món này)
        data['rest_id'] = ObjectId(data['rest_id'])
        # Thêm thời gian tạo vào dữ liệu
        data['created_at'] = datetime.now()
        # Chèn document mới vào collection menus
        result = get_db().menus.insert_one(data)
        # Trả về ID của menu vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def update(menu_id, data):
        """
        Cập nhật thông tin món ăn
        Tham số:
            menu_id (string) - ID của menu cần cập nhật
            data (dict) - Dictionary chứa các trường cần cập nhật
        Trả về: Kết quả của thao tác update
        """
        # Thêm thời gian cập nhật vào dữ liệu
        data['updated_at'] = datetime.now()
        # Nếu có rest_id trong data thì chuyển sang ObjectId
        if 'rest_id' in data:
            data['rest_id'] = ObjectId(data['rest_id'])
        # Cập nhật document có _id khớp với menu_id
        return get_db().menus.update_one(
            {"_id": ObjectId(menu_id)},  # Điều kiện tìm
            {"$set": data}  # Cập nhật các trường trong data
        )
    
    @staticmethod
    def delete(menu_id):
        """
        Xóa món ăn
        Tham số: menu_id (string) - ID của menu cần xóa
        Trả về: Kết quả của thao tác delete
        """
        # Xóa document có _id khớp với menu_id
        return get_db().menus.delete_one({"_id": ObjectId(menu_id)})

class Order:
    """Class Order - Model quản lý đơn hàng"""
    
    @staticmethod
    def find_by_user(user_id, limit=None):
        """
        Tìm tất cả đơn hàng của một khách hàng
        Tham số:
            user_id (string) - ID của khách hàng
            limit (int, optional) - Số lượng đơn hàng tối đa cần lấy
        Trả về: List các document order của user, sắp xếp theo thời gian tạo mới nhất trước
        """
        # Tìm đơn hàng có user_id khớp, sắp xếp theo created_at giảm dần (-1 = mới nhất trước)
        cursor = get_db().orders.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        # Nếu có giới hạn số lượng thì áp dụng limit
        if limit:
            cursor = cursor.limit(limit)
        # Chuyển cursor thành list và trả về
        return list(cursor)
    
    @staticmethod
    def find_by_id(order_id):
        """
        Tìm đơn hàng theo ID
        Tham số: order_id (string) - ID của order cần tìm
        Trả về: Document của order nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển order_id từ string sang ObjectId và tìm order có _id khớp
        return get_db().orders.find_one({"_id": ObjectId(order_id)})
    
    @staticmethod
    def find_available():
        """
        Tìm các đơn hàng chưa có shipper nhận (để shipper có thể nhận đơn)
        Trả về: List các order chưa có shipper và đang ở trạng thái pending hoặc preparing
        """
        # Tìm đơn hàng có shipper_id là None (chưa có tài xế) và status là pending hoặc preparing
        return list(get_db().orders.find({
            "shipper_id": None,  # Chưa có tài xế nhận
            "status": {"$in": ["pending", "preparing"]}  # Trạng thái đang chờ hoặc đang chuẩn bị
        }))
    
    @staticmethod
    def create(data):
        """
        Tạo đơn hàng mới
        Tham số: data (dict) - Dictionary chứa thông tin order (user_id, rest_id, items, total, v.v.)
        Trả về: ID của order vừa được tạo
        """
        # Chuyển user_id từ string sang ObjectId (ID của khách hàng đặt hàng)
        data['user_id'] = ObjectId(data['user_id'])
        # Chuyển rest_id từ string sang ObjectId (ID của nhà hàng)
        data['rest_id'] = ObjectId(data['rest_id'])
        # Thêm thời gian tạo vào dữ liệu
        data['created_at'] = datetime.now()
        # Chèn document mới vào collection orders
        result = get_db().orders.insert_one(data)
        # Trả về ID của order vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def update_status(order_id, status, shipper_id=None):
        """
        Cập nhật trạng thái đơn hàng và có thể gán shipper
        Tham số:
            order_id (string) - ID của order cần cập nhật
            status (string) - Trạng thái mới (pending, preparing, delivering, delivered, completed, cancelled)
            shipper_id (string, optional) - ID của shipper nếu cần gán tài xế
        Trả về: Kết quả của thao tác update
        """
        # Tạo dictionary chứa dữ liệu cần cập nhật
        update_data = {"status": status, "updated_at": datetime.now()}
        # Nếu có shipper_id thì thêm vào update_data (gán tài xế cho đơn hàng)
        if shipper_id:
            update_data["shipper_id"] = ObjectId(shipper_id)
        # Nếu status là completed thì thêm thời gian hoàn thành
        if status == 'completed':
            update_data["completed_at"] = datetime.now()
        # Cập nhật document có _id khớp với order_id
        return get_db().orders.update_one(
            {"_id": ObjectId(order_id)},  # Điều kiện tìm
            {"$set": update_data}  # Cập nhật trạng thái và shipper_id (nếu có)
        )
    
    @staticmethod
    def confirm_received(order_id, user_id):
        """
        Khách hàng xác nhận đã nhận hàng (chuyển từ delivered sang completed)
        Tham số:
            order_id (string) - ID của order
            user_id (string) - ID của khách hàng (để kiểm tra quyền)
        Trả về: Kết quả của thao tác update, hoặc None nếu không có quyền
        """
        # Tìm đơn hàng
        order = Order.find_by_id(order_id)
        # Kiểm tra đơn hàng có tồn tại và thuộc về user này không
        if not order or str(order.get('user_id')) != str(user_id):
            return None
        # Kiểm tra đơn hàng có status là 'delivered' không (chỉ cho phép xác nhận khi đã delivered)
        if order.get('status') != 'delivered':
            return None
        # Cập nhật status thành 'completed' và thêm thời gian hoàn thành
        return get_db().orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.now(),
                "updated_at": datetime.now()
            }}
        )

class Payment:
    """Class Payment - Model quản lý thanh toán"""
    
    @staticmethod
    def find_by_order(order_id):
        """
        Tìm thanh toán theo ID đơn hàng
        Tham số: order_id (string) - ID của order
        Trả về: Document của payment nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển order_id từ string sang ObjectId và tìm payment có order_id khớp
        return get_db().payments.find_one({"order_id": ObjectId(order_id)})
    
    @staticmethod
    def create(data):
        """
        Tạo bản ghi thanh toán mới
        Tham số: data (dict) - Dictionary chứa thông tin payment (order_id, amount, method, status, v.v.)
        Trả về: ID của payment vừa được tạo
        """
        # Chuyển order_id từ string sang ObjectId (ID của đơn hàng được thanh toán)
        data['order_id'] = ObjectId(data['order_id'])
        # Thêm thời gian tạo vào dữ liệu
        data['created_at'] = datetime.now()
        # Chèn document mới vào collection payments
        result = get_db().payments.insert_one(data)
        # Trả về ID của payment vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def update_status(payment_id, status):
        """
        Cập nhật trạng thái thanh toán
        Tham số:
            payment_id (string) - ID của payment cần cập nhật
            status (string) - Trạng thái mới (pending, completed, failed, refunded)
        Trả về: Kết quả của thao tác update
        """
        # Cập nhật document có _id khớp với payment_id, cập nhật status và updated_at
        return get_db().payments.update_one(
            {"_id": ObjectId(payment_id)},  # Điều kiện tìm
            {"$set": {"status": status, "updated_at": datetime.now()}}  # Cập nhật trạng thái và thời gian
        )

class Review:
    """Class Review - Model quản lý đánh giá (nhà hàng, shipper, món ăn)"""
    
    @staticmethod
    def create(data):
        """
        Tạo đánh giá mới
        Tham số: data (dict) - Dictionary chứa thông tin review (order_id, user_id, restaurant_id, 
                                restaurant_rating, restaurant_comment, shipper_id, driver_rating, 
                                driver_comment, menu_ratings, images, v.v.)
        Trả về: ID của review vừa được tạo
        """
        # Thêm thời gian tạo vào dữ liệu
        data['created_at'] = datetime.now()
        # Nếu có order_id và không rỗng thì chuyển sang ObjectId
        if 'order_id' in data and data['order_id']:
            data['order_id'] = ObjectId(data['order_id'])
        # Nếu có user_id và không rỗng thì chuyển sang ObjectId (ID của người đánh giá)
        if 'user_id' in data and data['user_id']:
            data['user_id'] = ObjectId(data['user_id'])
        # Nếu có restaurant_id và không rỗng thì chuyển sang ObjectId (ID của nhà hàng được đánh giá)
        if 'restaurant_id' in data and data['restaurant_id']:
            data['restaurant_id'] = ObjectId(data['restaurant_id'])
        # Nếu có shipper_id và không rỗng thì chuyển sang ObjectId (ID của tài xế được đánh giá)
        if 'shipper_id' in data and data['shipper_id']:
            data['shipper_id'] = ObjectId(data['shipper_id'])
        # Chuyển đổi menu_id trong menu_ratings từ string sang ObjectId
        if 'menu_ratings' in data and data['menu_ratings']:
            # Duyệt qua từng đánh giá món ăn trong danh sách
            for menu_rating in data['menu_ratings']:
                # Nếu có menu_id và không rỗng thì chuyển sang ObjectId
                if 'menu_id' in menu_rating and menu_rating['menu_id']:
                    menu_rating['menu_id'] = ObjectId(menu_rating['menu_id'])
        # Chèn document mới vào collection reviews
        result = get_db().reviews.insert_one(data)
        # Trả về ID của review vừa được tạo
        return result.inserted_id
    
    @staticmethod
    def find_by_order(order_id):
        """
        Tìm đánh giá theo ID đơn hàng
        Tham số: order_id (string) - ID của order
        Trả về: Document của review nếu tìm thấy, None nếu không tìm thấy
        """
        # Chuyển order_id từ string sang ObjectId và tìm review có order_id khớp
        return get_db().reviews.find_one({"order_id": ObjectId(order_id)})
    
    @staticmethod
    def find_by_restaurant(rest_id):
        """
        Tìm tất cả đánh giá của một nhà hàng
        Tham số: rest_id (string) - ID của restaurant
        Trả về: List các document review của nhà hàng, sắp xếp theo thời gian tạo mới nhất trước
        """
        # Tìm tất cả review có restaurant_id khớp, sắp xếp theo created_at giảm dần
        return list(get_db().reviews.find({"restaurant_id": ObjectId(rest_id)}).sort("created_at", -1))
    
    @staticmethod
    def find_by_shipper(shipper_id):
        """
        Tìm tất cả đánh giá của một shipper (tài xế)
        Tham số: shipper_id (string) - ID của shipper
        Trả về: List các document review của shipper, sắp xếp theo thời gian tạo mới nhất trước
        """
        # Tìm tất cả review có shipper_id khớp, sắp xếp theo created_at giảm dần
        return list(get_db().reviews.find({"shipper_id": ObjectId(shipper_id)}).sort("created_at", -1))
    
    @staticmethod
    def find_by_menu(menu_id):
        """
        Tìm tất cả đánh giá có chứa một món ăn cụ thể
        Tham số: menu_id (string) - ID của menu
        Trả về: List các document review có chứa đánh giá món ăn này, sắp xếp theo thời gian tạo mới nhất trước
        """
        # Tìm tất cả review có menu_ratings chứa menu_id khớp (tìm trong nested array)
        # menu_ratings.menu_id là cách truy cập trường nested trong MongoDB
        return list(get_db().reviews.find({"menu_ratings.menu_id": ObjectId(menu_id)}).sort("created_at", -1))
    
    @staticmethod
    def calculate_restaurant_rating(rest_id):
        """
        Tính điểm đánh giá trung bình của nhà hàng
        Tham số: rest_id (string) - ID của restaurant
        Trả về: Điểm trung bình (float) từ 0.0 đến 5.0, làm tròn 1 chữ số thập phân
        """
        # Lấy tất cả đánh giá của nhà hàng
        reviews = Review.find_by_restaurant(rest_id)
        # Nếu không có đánh giá nào thì trả về 0.0
        if not reviews:
            return 0.0
        
        # Tính tổng điểm đánh giá (lấy restaurant_rating từ mỗi review, mặc định là 0 nếu không có)
        total_rating = sum(r.get('restaurant_rating', 0) for r in reviews)
        # Tính trung bình và làm tròn 1 chữ số thập phân
        return round(total_rating / len(reviews), 1)
    
    @staticmethod
    def calculate_shipper_rating(shipper_id):
        """
        Tính điểm đánh giá trung bình của shipper (tài xế)
        Tham số: shipper_id (string) - ID của shipper
        Trả về: Điểm trung bình (float) từ 0.0 đến 5.0, làm tròn 1 chữ số thập phân
        """
        # Lấy tất cả đánh giá của shipper
        reviews = Review.find_by_shipper(shipper_id)
        # Nếu không có đánh giá nào thì trả về 0.0
        if not reviews:
            return 0.0
        
        # Tính tổng điểm đánh giá (lấy driver_rating từ mỗi review, mặc định là 0 nếu không có)
        total_rating = sum(r.get('driver_rating', 0) for r in reviews)
        # Tính trung bình và làm tròn 1 chữ số thập phân
        return round(total_rating / len(reviews), 1)
    
    @staticmethod
    def count_zero_star_reviews(shipper_id):
        """
        Đếm số lần đánh giá 0 sao của shipper (dùng để kiểm tra có nên ban shipper không)
        Tham số: shipper_id (string) - ID của shipper
        Trả về: Số lượng đánh giá 0 sao (int)
        """
        # Đếm số document review có shipper_id khớp và driver_rating = 0
        return get_db().reviews.count_documents({
            "shipper_id": ObjectId(shipper_id),  # ID của shipper
            "driver_rating": 0  # Đánh giá 0 sao
        })

