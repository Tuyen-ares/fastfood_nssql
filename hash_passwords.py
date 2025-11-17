"""
Script để hash lại tất cả password trong database
Chạy script này để chuyển đổi password từ plain text sang bcrypt hash
"""
from app import create_app
from app.database import get_db
from app import bcrypt

app = create_app()

with app.app_context():
    db = get_db()
    users = db.users.find({})
    
    updated_count = 0
    skipped_count = 0
    
    for user in users:
        password = user.get('password', '')
        
        # Kiểm tra xem password đã được hash chưa
        is_bcrypt_hash = password.startswith('$2a$') or password.startswith('$2b$')
        
        if not is_bcrypt_hash and password:
            # Password là plain text, hash lại
            try:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'password': hashed_password}}
                )
                print(f"✅ Đã hash password cho user: {user.get('phone', 'N/A')} ({user.get('name', 'N/A')})")
                updated_count += 1
            except Exception as e:
                print(f"❌ Lỗi khi hash password cho user {user.get('phone', 'N/A')}: {str(e)}")
        else:
            print(f"⏭️  Bỏ qua user {user.get('phone', 'N/A')} - password đã được hash")
            skipped_count += 1
    
    print(f"\n📊 Tổng kết:")
    print(f"   - Đã hash: {updated_count} user(s)")
    print(f"   - Đã bỏ qua: {skipped_count} user(s)")
    print(f"   - Tổng cộng: {updated_count + skipped_count} user(s)")

