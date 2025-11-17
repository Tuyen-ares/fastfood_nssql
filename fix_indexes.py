"""
Script để xóa và tạo lại indexes đúng cách
Chạy script này một lần để fix lỗi duplicate key
"""
from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fastfood']

print("🔧 Đang sửa indexes...")

try:
    # Xóa index unique cũ trên payments.order_id (nếu có)
    try:
        db.payments.drop_index("order_id_1")
        print("✅ Đã xóa index unique cũ trên payments.order_id")
    except Exception as e:
        print(f"ℹ️ Index chưa tồn tại hoặc đã được xóa: {e}")
    
    # Tạo lại index không unique
    db.payments.create_index("order_id")
    print("✅ Đã tạo lại index thông thường trên payments.order_id")
    
    # Tạo các indexes khác nếu chưa có
    db.payments.create_index("status")
    print("✅ Đã tạo index trên payments.status")
    
    print("\n✅ Hoàn tất! Bây giờ bạn có thể chạy lại Flask app.")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")

