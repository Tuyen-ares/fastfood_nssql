# Import module os để truy cập biến môi trường
import os
# Import timedelta để cấu hình thời gian session
from datetime import timedelta

class Config:
    # Cấu hình Flask
    # Lấy SECRET_KEY từ biến môi trường, nếu không có thì dùng giá trị mặc định (chỉ dùng cho development)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cấu hình MongoDB
    # Lấy địa chỉ host MongoDB từ biến môi trường, mặc định là localhost
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or 'localhost'
    # Lấy cổng kết nối MongoDB từ biến môi trường và chuyển sang số nguyên, mặc định là 27017
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT') or 27017)
    # Lấy tên database từ biến môi trường, mặc định là 'fastfood'
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'fastfood'
    # Tạo chuỗi kết nối MongoDB từ các thông tin trên, hoặc lấy từ biến môi trường nếu có
    MONGODB_URI = os.environ.get('MONGODB_URI') or f'mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}'
    
    # Cấu hình Session
    # Thời gian sống của session là 24 giờ
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Cấu hình Phân trang
    # Số lượng item hiển thị trên mỗi trang
    ITEMS_PER_PAGE = 20
    
    # Cấu hình Upload File
    # Thư mục lưu trữ file upload (hình ảnh menu)
    UPLOAD_FOLDER = 'static/uploads/menus'
    # Kích thước file tối đa cho phép upload: 16MB (16 * 1024 * 1024 bytes)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    # Các định dạng file hình ảnh được phép upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Cấu hình Thanh toán - VnPay
    # ============================================
    # CẤU HÌNH VNPAY - Thay thế các giá trị bên dưới:
    # ============================================
    # Tài liệu: https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
    # Bước 1: Đăng ký tại https://sandbox.vnpayment.vn/devreg/
    # Bước 2: Lấy TMN Code và Hash Secret từ email VnPay gửi về
    # Bước 3: Thay thế 'YOUR_TMN_CODE' và 'YOUR_HASH_SECRET' bên dưới
    # ============================================
    # ============================================
    # THÔNG TIN TỪ EMAIL VNPAY (ĐÃ CẬP NHẬT)
    # ============================================
    # Mã Terminal ID từ email VnPay gửi về sau khi đăng ký
    VNPAY_TMN_CODE = 'COT8FR64'
    # Secret Key (khóa bí mật) từ email VnPay để mã hóa dữ liệu thanh toán
    VNPAY_HASH_SECRET = 'G91OXLUD6QZVBADKVZPDL7JTNFCZJAGB'
    # URL của trang thanh toán VnPay (môi trường Sandbox để test)
    VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
    # ============================================
    # CẤU HÌNH URL CALLBACK
    # ============================================
    # Nếu dùng Ngrok: Thay bằng URL từ Ngrok (ví dụ: https://abc123.ngrok.io)
    # Nếu đã deploy: Thay bằng domain thật (ví dụ: https://yourdomain.com)
    # Nếu test local: Có thể dùng localhost nhưng cần cấu hình trong VnPay Portal
    # URL mà VnPay sẽ redirect về sau khi khách hàng thanh toán xong
    VNPAY_RETURN_URL = 'http://localhost:5000/customer/payment/vnpay_return'
    # URL IPN (Instant Payment Notification) - VnPay gọi đến server để thông báo kết quả thanh toán (server-to-server)
    VNPAY_IPN_URL = 'http://localhost:5000/customer/payment/vnpay_ipn'

