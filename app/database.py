# Import thư viện MongoClient từ pymongo để tạo kết nối đến MongoDB
from pymongo import MongoClient
# Import lớp lỗi ConnectionFailure để xử lý khi kết nối thất bại
from pymongo.errors import ConnectionFailure
# Import current_app từ Flask để truy cập cấu hình ứng dụng
from flask import current_app

# Khai báo biến global để lưu trữ client MongoDB (kết nối đến server)
client = None
# Khai báo biến global để lưu trữ database instance (kết nối đến database cụ thể)
db = None

def init_db(app):
    """Khởi tạo kết nối MongoDB"""
    # Khai báo sử dụng biến global để có thể thay đổi giá trị từ trong hàm
    global client, db
    
    try:
        # Tạo kết nối đến MongoDB server sử dụng URI từ cấu hình ứng dụng
        client = MongoClient(app.config['MONGODB_URI'])
        # Chọn database cụ thể từ tên database trong cấu hình
        db = client[app.config['MONGODB_DB']]
        
        # Kiểm tra kết nối bằng lệnh ping đến admin database
        client.admin.command('ping')
        # In thông báo thành công khi kết nối được thiết lập
        print(f"Connected to MongoDB: {app.config['MONGODB_DB']}")
        
        # Gọi hàm tạo các index để tối ưu hiệu suất truy vấn
        create_indexes(db)
        
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def create_indexes(database):
    """Tạo các index cho database để tối ưu hiệu suất truy vấn"""
    try:
        # Tạo index cho collection users
        try:
            # Tạo index unique cho trường phone để đảm bảo số điện thoại không trùng lặp
            database.users.create_index("phone", unique=True)
        except Exception as e:
            # Nếu index đã tồn tại hoặc có lỗi thì in cảnh báo nhưng không dừng chương trình
            print(f"Warning: Index users.phone already exists or error: {e}")
        
        # Tạo index cho trường role để tìm kiếm người dùng theo vai trò nhanh hơn
        database.users.create_index("role")
        # Tạo index cho trường status để lọc người dùng theo trạng thái nhanh hơn
        database.users.create_index("status")
        
        # Tạo index cho collection restaurants
        try:
            # Tạo index địa lý 2dsphere cho trường loc để hỗ trợ tìm kiếm theo vị trí (geospatial queries)
            database.restaurants.create_index([("loc", "2dsphere")])
        except Exception as e:
            # Nếu index đã tồn tại hoặc có lỗi thì in cảnh báo
            print(f"Warning: Index restaurants.loc already exists or error: {e}")
        
        # Tạo index cho trường status để lọc nhà hàng theo trạng thái
        database.restaurants.create_index("status")
        # Tạo index cho trường name để tìm kiếm nhà hàng theo tên nhanh hơn
        database.restaurants.create_index("name")
        # Tạo index cho trường owner_id để tìm nhà hàng theo chủ sở hữu
        database.restaurants.create_index("owner_id")
        
        # Tạo index cho collection menus
        # Tạo index cho trường rest_id để tìm menu theo nhà hàng nhanh hơn
        database.menus.create_index("rest_id")
        # Tạo index cho trường status để lọc menu theo trạng thái
        database.menus.create_index("status")
        
        # Tạo index cho collection orders
        # Tạo index cho trường user_id để tìm đơn hàng theo khách hàng
        database.orders.create_index("user_id")
        # Tạo index cho trường rest_id để tìm đơn hàng theo nhà hàng
        database.orders.create_index("rest_id")
        # Tạo index cho trường shipper_id để tìm đơn hàng theo tài xế
        database.orders.create_index("shipper_id")
        # Tạo index cho trường status để lọc đơn hàng theo trạng thái
        database.orders.create_index("status")
        # Tạo index cho trường created_at để sắp xếp đơn hàng theo thời gian tạo
        database.orders.create_index("created_at")
        
        # Tạo index cho collection payments
        # Lưu ý: Không đặt unique vì một đơn hàng có thể có nhiều thanh toán (hoàn tiền, v.v.)
        # Tạo index cho trường order_id để tìm thanh toán theo đơn hàng
        database.payments.create_index("order_id")
        # Tạo index cho trường status để lọc thanh toán theo trạng thái
        database.payments.create_index("status")
        
        # Tạo index cho collection reviews
        # Xóa index cũ nếu tồn tại và tạo lại với unique
        try:
            # Thử xóa index cũ có tên "order_id_1" nếu có
            database.reviews.drop_index("order_id_1")
        except Exception:
            # Nếu index không tồn tại thì bỏ qua, không cần xử lý
            pass
        
        try:
            # Tạo index unique cho trường order_id để đảm bảo mỗi đơn hàng chỉ có 1 đánh giá
            database.reviews.create_index("order_id", unique=True, name="order_id_unique")
        except Exception as e:
            # Nếu index đã tồn tại hoặc có lỗi thì in cảnh báo
            print(f"Warning: Index reviews.order_id already exists or error: {e}")
        
        # Tạo index cho trường restaurant_id để tìm đánh giá theo nhà hàng
        database.reviews.create_index("restaurant_id")
        # Tạo index cho trường shipper_id để tìm đánh giá theo tài xế
        database.reviews.create_index("shipper_id")
        # Tạo index cho trường user_id để tìm đánh giá theo người dùng
        database.reviews.create_index("user_id")
        # Tạo index cho trường created_at để sắp xếp đánh giá theo thời gian
        database.reviews.create_index("created_at")
        # Tạo index cho trường menu_ratings.menu_id (nested field) để tìm đánh giá món ăn nhanh hơn
        database.reviews.create_index("menu_ratings.menu_id")
        
        # In thông báo thành công khi tạo xong tất cả index
        print("Database indexes created successfully")
        
    except Exception as e:
        # Bắt mọi lỗi khác và in cảnh báo nhưng không dừng chương trình
        print(f"Warning: Could not create all indexes: {e}")

def get_db():
    """Lấy instance database để sử dụng trong các route và hàm khác"""
    # Trả về biến global db đã được khởi tạo trong hàm init_db
    return db

