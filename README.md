# FastFood Delivery System

Hệ thống giao thức ăn nhanh sử dụng Flask và MongoDB (NoSQL)

## Công nghệ sử dụng

- **Backend**: Flask (Python)
- **Database**: MongoDB (NoSQL)
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## Cài đặt

### 1. Kiểm tra MongoDB

Đảm bảo MongoDB đã được cài đặt và đang chạy:

**Cách 1: Kiểm tra bằng Python (Khuyến nghị)**

```bash
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB connected!'); print('Databases:', client.list_database_names())"
```

**Cách 2: Sử dụng MongoDB Compass**

- Mở MongoDB Compass
- Kết nối đến `mongodb://localhost:27017`
- Kiểm tra database `fastfood` đã tồn tại chưa

### 2. Tạo môi trường ảo (Virtual Environment)

```bash
# Tạo virtual environment
python -m venv venv
```

**Kích hoạt virtual environment:**

**Windows - PowerShell:**

```powershell
# Cách 1: Sử dụng activate.bat (Khuyến nghị)
venv\Scripts\activate.bat

# Cách 2: Bypass execution policy cho session hiện tại
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
venv\Scripts\activate

# Cách 3: Sử dụng Command Prompt (cmd) thay vì PowerShell
# Mở cmd và chạy:
venv\Scripts\activate
```

**Windows - Command Prompt (cmd):**

```cmd
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

**Lưu ý:** Nếu gặp lỗi `PSSecurityException` trong PowerShell, sử dụng `activate.bat` hoặc chuyển sang Command Prompt.

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình

Tạo file `.env` (tùy chọn) hoặc sử dụng cấu hình mặc định trong `app/config.py`:

```env
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=fastfood
SECRET_KEY=your-secret-key-here
```

### 5. Khởi tạo Database

**Cách 1: Sử dụng MongoDB Compass (Khuyến nghị)**

1. Mở MongoDB Compass
2. Kết nối đến `mongodb://localhost:27017`
3. Chọn database `fastfood` (hoặc tạo mới nếu chưa có)
4. Vào tab "My Queries" hoặc "Aggregations"
5. Copy toàn bộ nội dung từ file `db_nosql.txt`
6. Paste vào MongoDB Compass và chạy script

**Cách 2: Sử dụng MongoDB Shell**

```bash
# Kết nối MongoDB
mongosh

# Chọn database
use fastfood

# Copy và paste nội dung từ file db_nosql.txt vào shell
```

**Lưu ý:** Nếu database `fastfood` đã có dữ liệu, bạn có thể xóa và tạo lại:

```javascript
// Trong MongoDB Compass hoặc mongosh
use fastfood
db.dropDatabase()
// Sau đó chạy lại script từ db_nosql.txt
```

### 6. Chạy ứng dụng

```bash
python run.py
```

Truy cập: <http://localhost:5000>

## Cấu trúc Project

```
DoAn/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config.py            # Configuration
│   ├── database.py          # MongoDB connection
│   ├── models.py            # Database models
│   ├── routes/              # Routes
│   │   ├── auth.py         # Authentication
│   │   ├── customer.py     # Customer routes
│   │   ├── admin.py        # Admin routes
│   │   ├── shipper.py      # Shipper routes
│   │   └── main.py         # Main routes
│   └── utils/              # Utilities
│       ├── auth.py         # Auth helpers
│       └── helpers.py       # Helper functions
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
├── run.py                   # Entry point
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Tài khoản mặc định

Sau khi chạy script `db_nosql.txt`:

- **Admin**:
  - Phone: 0999999999
  - Password: admin123

- **Customer**:
  - Phone: 0901000001
  - Password: nam123

- **Shipper**:
  - Phone: 0888888888
  - Password: ship123

## Chức năng

### Admin

- Quản lý users, restaurants, shippers
- Duyệt nhà hàng và tài xế mới
- Quản lý đơn hàng
- Thống kê và báo cáo

### Customer

- Tìm kiếm và xem nhà hàng
- Xem menu và thêm vào giỏ hàng
- Đặt hàng và thanh toán
- Theo dõi đơn hàng

### Shipper

- Nhận đơn hàng
- Cập nhật trạng thái giao hàng
- Xem thống kê thu nhập

## Kiểm tra kết nối MongoDB

Sau khi chạy script `db_nosql.txt`, kiểm tra dữ liệu đã được tạo:

```python
# Chạy trong Python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['fastfood']

print("Users:", db.users.count_documents({}))
print("Restaurants:", db.restaurants.count_documents({}))
print("Menus:", db.menus.count_documents({}))
print("Orders:", db.orders.count_documents({}))
```

Hoặc kiểm tra trong MongoDB Compass:

- Mở database `fastfood`
- Xem các collections: users, restaurants, menus, orders, payments

## Development

```bash
# Chạy với debug mode (Windows)
python run.py

# Hoặc (Linux/Mac)
export FLASK_ENV=development
python run.py
```

## License

Đồ án môn học NoSQL - HK7
