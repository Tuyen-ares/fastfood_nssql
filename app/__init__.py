# Import Flask để tạo ứng dụng web
from flask import Flask
# Import Bcrypt để mã hóa mật khẩu
from flask_bcrypt import Bcrypt
# Import class Config chứa các cấu hình của ứng dụng
from app.config import Config
# Import hàm init_db để khởi tạo kết nối MongoDB
from app.database import init_db

# Tạo instance của Bcrypt để sử dụng mã hóa mật khẩu
bcrypt = Bcrypt()

def create_app(config_class=Config):
    # Import os để xử lý đường dẫn file
    import os
    # Lấy đường dẫn tuyệt đối đến thư mục templates (thư mục chứa file HTML)
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    # Lấy đường dẫn tuyệt đối đến thư mục static (thư mục chứa CSS, JS, hình ảnh)
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    # Tạo ứng dụng Flask với tên module hiện tại và chỉ định thư mục templates và static
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    # Nạp cấu hình từ class Config vào ứng dụng Flask
    app.config.from_object(config_class)
    
    # Khởi tạo các extension (tiện ích mở rộng)
    # Khởi tạo Bcrypt với ứng dụng Flask để có thể sử dụng mã hóa mật khẩu
    bcrypt.init_app(app)
    
    # Khởi tạo kết nối database MongoDB
    # Gọi hàm init_db để tạo kết nối đến MongoDB và tạo các index
    init_db(app)
    
    # Đăng ký các blueprint (nhóm route) cho ứng dụng
    # Import blueprint xử lý xác thực (đăng nhập, đăng ký)
    from app.routes.auth import auth_bp
    # Import blueprint xử lý các chức năng của khách hàng
    from app.routes.customer import customer_bp
    # Import blueprint xử lý các chức năng của admin
    from app.routes.admin import admin_bp
    # Import blueprint xử lý các chức năng của shipper (tài xế)
    from app.routes.shipper import shipper_bp
    # Import blueprint xử lý các chức năng của restaurant owner (chủ nhà hàng)
    from app.routes.restaurant import restaurant_bp
    # Import blueprint xử lý các route chính (trang chủ, v.v.)
    from app.routes.main import main_bp
    
    # Đăng ký blueprint xác thực vào ứng dụng Flask
    app.register_blueprint(auth_bp)
    # Đăng ký blueprint khách hàng vào ứng dụng Flask
    app.register_blueprint(customer_bp)
    # Đăng ký blueprint admin vào ứng dụng Flask
    app.register_blueprint(admin_bp)
    # Đăng ký blueprint shipper vào ứng dụng Flask
    app.register_blueprint(shipper_bp)
    # Đăng ký blueprint restaurant vào ứng dụng Flask
    app.register_blueprint(restaurant_bp)
    # Đăng ký blueprint main vào ứng dụng Flask
    app.register_blueprint(main_bp)
    
    # Trả về ứng dụng Flask đã được cấu hình đầy đủ
    return app

