# CHƯƠNG 5: XÂY DỰNG ỨNG DỤNG MINH HỌA KẾT NỐI VỚI DATABASE

## 1. Giới thiệu chung

Sau khi đã phân tích và thiết kế cơ sở dữ liệu "Giao thức ăn nhanh" cũng như tìm hiểu các chức năng quản trị trong Studio 3T, bước tiếp theo là xây dựng một ứng dụng minh họa giúp kết nối, thao tác và hiển thị dữ liệu thực tế từ MongoDB.

**Mục tiêu của chương này là:**

- Trình bày cách ứng dụng kết nối với MongoDB thông qua thư viện lập trình PyMongo
- Thực hiện các thao tác cơ bản như thêm, sửa, xóa, xem dữ liệu (CRUD operations)
- Kiểm thử khả năng kết nối và xử lý lỗi khi kết nối thất bại
- Trình bày giao diện web mô phỏng ứng dụng quản lý đơn hàng của cửa hàng thức ăn nhanh
- Minh họa cách tạo và sử dụng các index để tối ưu hiệu suất truy vấn

Ứng dụng minh họa đóng vai trò cầu nối giữa lớp quản lý dữ liệu (MongoDB) và người dùng cuối (End User), giúp hình dung cách một hệ thống thực tế hoạt động dựa trên cơ sở dữ liệu đã thiết kế.

---

## 2. Công nghệ sử dụng

Ứng dụng được xây dựng với mục tiêu đơn giản, dễ hiểu và minh họa rõ ràng cách kết nối MongoDB. Các công nghệ được sử dụng bao gồm:

| Thành Phần | Công nghệ/ Công cụ |
|------------|-------------------|
| **Ngôn ngữ lập trình** | Python 3.x |
| **Môi trường phát triển** | Visual Studio Code / PyCharm |
| **Framework web** | Flask (Micro web framework) |
| **Giao diện người dùng** | HTML, CSS (Bootstrap), JavaScript |
| **Template Engine** | Jinja2 (tích hợp sẵn trong Flask) |
| **Cơ sở dữ liệu** | MongoDB |
| **Công cụ quản lý dữ liệu** | Studio 3T / MongoDB Compass |
| **Thư viện kết nối** | PyMongo (thư viện chính thức của MongoDB cho Python) |
| **Thư viện mã hóa mật khẩu** | Flask-Bcrypt |
| **Thư viện xử lý file** | Werkzeug |

**PyMongo** giúp ứng dụng Python giao tiếp trực tiếp với cơ sở dữ liệu MongoDB thông qua các lệnh truy vấn, insert, update, delete… tương tự như cách ta thao tác bằng Studio 3T.

---

## 3. Cách kết nối ứng dụng với MongoDB

### 3.1. Cài đặt thư viện PyMongo

Để kết nối được với MongoDB, ứng dụng cần cài đặt gói thư viện PyMongo thông qua pip (Python Package Manager).

**Các bước cài đặt:**

1. Mở terminal/command prompt
2. Di chuyển đến thư mục project
3. Tạo virtual environment (khuyến nghị):

   ```bash
   python -m venv venv
   ```

4. Kích hoạt virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
5. Cài đặt các thư viện cần thiết:

   ```bash
   pip install -r requirements.txt
   ```

**File `requirements.txt` chứa các thư viện:**

```
Flask==3.0.0
Flask-Bcrypt==1.0.1
pymongo==4.6.0
Werkzeug==3.0.1
```

**Cấu trúc thư viện sau khi cài đặt:**

- `pymongo`: Thư viện chính để kết nối MongoDB
- `flask`: Framework web
- `flask-bcrypt`: Mã hóa mật khẩu
- `werkzeug`: Công cụ hỗ trợ Flask (xử lý file upload, security)

### 3.2. Cấu hình kết nối MongoDB

#### 3.2.1. File cấu hình: `app/config.py`

File này chứa tất cả các cấu hình của ứng dụng, bao gồm thông tin kết nối MongoDB:

```python
import os
from datetime import timedelta

class Config:
    # Cấu hình Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cấu hình MongoDB
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or 'localhost'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT') or 27017)
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'fastfood'
    MONGODB_URI = os.environ.get('MONGODB_URI') or f'mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}'
    
    # Cấu hình Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Cấu hình Upload File
    UPLOAD_FOLDER = 'static/uploads/menus'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
```

**Giải thích:**

- `MONGODB_HOST`: Địa chỉ máy chủ MongoDB (mặc định: localhost)
- `MONGODB_PORT`: Cổng kết nối MongoDB (mặc định: 27017)
- `MONGODB_DB`: Tên database (mặc định: fastfood)
- `MONGODB_URI`: Chuỗi kết nối đầy đủ đến MongoDB

#### 3.2.2. File kết nối: `app/database.py`

Đây là file quan trọng nhất, chứa logic kết nối MongoDB:

```python
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flask import current_app

# Khai báo biến global để lưu trữ client và database
client = None
db = None

def init_db(app):
    """Khởi tạo kết nối MongoDB"""
    global client, db
    
    try:
        # Tạo kết nối đến MongoDB server sử dụng URI từ cấu hình
        client = MongoClient(app.config['MONGODB_URI'])
        # Chọn database cụ thể
        db = client[app.config['MONGODB_DB']]
        
        # Kiểm tra kết nối bằng lệnh ping
        client.admin.command('ping')
        print(f"Connected to MongoDB: {app.config['MONGODB_DB']}")
        
        # Tạo các index để tối ưu hiệu suất
        create_indexes(db)
        
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def get_db():
    """Lấy instance database để sử dụng trong các route"""
    return db

def create_indexes(database):
    """Tạo các index cho database để tối ưu hiệu suất truy vấn"""
    try:
        # Index cho collection users
        database.users.create_index("phone", unique=True)
        database.users.create_index("role")
        database.users.create_index("status")
        
        # Index cho collection restaurants (geospatial index)
        database.restaurants.create_index([("loc", "2dsphere")])
        database.restaurants.create_index("status")
        database.restaurants.create_index("name")
        database.restaurants.create_index("owner_id")
        
        # Index cho collection menus
        database.menus.create_index("rest_id")
        database.menus.create_index("status")
        
        # Index cho collection orders
        database.orders.create_index("user_id")
        database.orders.create_index("rest_id")
        database.orders.create_index("shipper_id")
        database.orders.create_index("status")
        database.orders.create_index("created_at")
        
        # Index cho collection payments
        database.payments.create_index("order_id")
        database.payments.create_index("status")
        
        # Index cho collection reviews
        database.reviews.create_index("order_id", unique=True)
        database.reviews.create_index("restaurant_id")
        database.reviews.create_index("shipper_id")
        database.reviews.create_index("user_id")
        database.reviews.create_index("created_at")
        database.reviews.create_index("menu_ratings.menu_id")
        
        print("Database indexes created successfully")
        
    except Exception as e:
        print(f"Warning: Could not create all indexes: {e}")
```

**Giải thích các hàm:**

1. **`init_db(app)`**:
   - Khởi tạo kết nối MongoDB khi ứng dụng khởi động
   - Tạo `MongoClient` với URI từ cấu hình
   - Chọn database cụ thể
   - Kiểm tra kết nối bằng lệnh `ping`
   - Tự động tạo các index để tối ưu hiệu suất

2. **`get_db()`**:
   - Trả về instance database đã được khởi tạo
   - Được sử dụng trong các route và model để thao tác với database

3. **`create_indexes(database)`**:
   - Tạo các index trên các trường thường xuyên được truy vấn
   - Giúp tăng tốc độ tìm kiếm và sắp xếp dữ liệu
   - Index `2dsphere` cho phép tìm kiếm theo vị trí địa lý (geospatial queries)

#### 3.2.3. Khởi tạo ứng dụng: `app/__init__.py`

File này khởi tạo Flask application và gọi hàm kết nối database:

```python
from flask import Flask
from flask_bcrypt import Bcrypt
from app.config import Config
from app.database import init_db

bcrypt = Bcrypt()

def create_app(config_class=Config):
    # Tạo Flask application
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Khởi tạo Bcrypt (mã hóa mật khẩu)
    bcrypt.init_app(app)
    
    # Khởi tạo kết nối MongoDB
    init_db(app)
    
    # Đăng ký các blueprint (routes)
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.admin import admin_bp
    from app.routes.shipper import shipper_bp
    from app.routes.restaurant import restaurant_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shipper_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(main_bp)
    
    return app
```

**Luồng khởi tạo:**

1. Tạo Flask app
2. Nạp cấu hình từ `Config` class
3. Khởi tạo Bcrypt
4. **Gọi `init_db(app)` để kết nối MongoDB**
5. Đăng ký các blueprint (routes)

### 3.3. Kiểm thử kết nối

#### 3.3.1. Chạy ứng dụng

File `run.py` là entry point của ứng dụng:

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Cách chạy:**

```bash
python run.py
```

**Kết quả mong đợi khi kết nối thành công:**

```
Connected to MongoDB: fastfood
Database indexes created successfully
 * Running on http://0.0.0.0:5000
```

#### 3.3.2. Xử lý lỗi kết nối

Nếu MongoDB không chạy hoặc cấu hình sai, sẽ có thông báo lỗi:

```
Failed to connect to MongoDB: [Errno 10061] No connection could be made because the target machine actively refused it
```

**Các lỗi thường gặp và cách xử lý:**

1. **Lỗi: MongoDB không chạy**
   - **Nguyên nhân:** Service MongoDB chưa được khởi động
   - **Giải pháp:** Khởi động MongoDB service:

     ```bash
     # Windows (Service)
     net start MongoDB
     
     # Linux/Mac
     sudo systemctl start mongod
     # hoặc
     mongod
     ```

2. **Lỗi: Sai cổng kết nối**
   - **Nguyên nhân:** Cổng MongoDB không đúng (mặc định: 27017)
   - **Giải pháp:** Kiểm tra và sửa `MONGODB_PORT` trong `app/config.py`

3. **Lỗi: Database không tồn tại**
   - **Nguyên nhân:** Tên database trong cấu hình không khớp
   - **Giải pháp:** Tạo database trong MongoDB hoặc sửa `MONGODB_DB` trong `app/config.py`

4. **Lỗi: Index đã tồn tại**
   - **Nguyên nhân:** Index đã được tạo trước đó
   - **Giải pháp:** Code đã xử lý tự động, chỉ in cảnh báo, không ảnh hưởng đến ứng dụng

---

## 4. Các chức năng chính của ứng dụng

### 4.1. Kiến trúc ứng dụng

Ứng dụng được xây dựng theo mô hình **MVC (Model-View-Controller)**:

- **Model** (`app/models.py`): Định nghĩa các class để thao tác với database
- **View** (`templates/`): Các file HTML hiển thị giao diện
- **Controller** (`app/routes/`): Xử lý logic và điều hướng

**Cấu trúc thư mục:**

```
DoAn/
├── app/
│   ├── __init__.py          # Khởi tạo Flask app
│   ├── config.py            # Cấu hình ứng dụng
│   ├── database.py          # Kết nối MongoDB
│   ├── models.py            # Model classes (User, Restaurant, Order, ...)
│   ├── routes/              # Controllers (routes)
│   │   ├── auth.py          # Xác thực (đăng nhập, đăng ký)
│   │   ├── customer.py      # Chức năng khách hàng
│   │   ├── shipper.py       # Chức năng tài xế
│   │   ├── restaurant.py    # Chức năng chủ nhà hàng
│   │   ├── admin.py         # Chức năng admin
│   │   └── main.py          # Trang chủ, public routes
│   └── utils/               # Tiện ích hỗ trợ
│       ├── auth.py          # Xác thực người dùng
│       ├── helpers.py       # Hàm tiện ích
│       └── vnpay.py         # Xử lý thanh toán VNPay
├── templates/               # HTML templates
│   ├── base.html            # Template cơ sở
│   ├── customer/            # Templates cho khách hàng
│   ├── shipper/             # Templates cho tài xế
│   ├── restaurant/          # Templates cho chủ nhà hàng
│   └── admin/               # Templates cho admin
├── static/                  # CSS, JS, hình ảnh
├── run.py                   # Entry point
└── requirements.txt         # Dependencies
```

### 4.2. Model Layer - Tương tác với Database

#### 4.2.1. Class User

Quản lý người dùng (khách hàng, admin, shipper, chủ nhà hàng):

```python
class User:
    """Class User - Model quản lý người dùng"""
    
    @staticmethod
    def find_by_phone(phone):
        """Tìm người dùng theo số điện thoại"""
        return get_db().users.find_one({"phone": phone})
    
    @staticmethod
    def find_by_id(user_id):
        """Tìm người dùng theo ID"""
        return get_db().users.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def create(data):
        """Tạo người dùng mới"""
        data['created_at'] = datetime.now()
        result = get_db().users.insert_one(data)
        return result.inserted_id
    
    @staticmethod
    def update(user_id, data):
        """Cập nhật thông tin người dùng"""
        data['updated_at'] = datetime.now()
        return get_db().users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data}
        )
```

**Các thao tác CRUD:**

- **Create**: `User.create(data)` - Tạo user mới
- **Read**: `User.find_by_id()`, `User.find_by_phone()` - Tìm user
- **Update**: `User.update(user_id, data)` - Cập nhật user
- **Delete**: Có thể thêm method `User.delete(user_id)` nếu cần

#### 4.2.2. Class Restaurant

Quản lý nhà hàng:

```python
class Restaurant:
    """Class Restaurant - Model quản lý nhà hàng"""
    
    @staticmethod
    def find_by_id(rest_id):
        """Tìm nhà hàng theo ID"""
        return get_db().restaurants.find_one({"_id": ObjectId(rest_id)})
    
    @staticmethod
    def find_nearby(lat, lng, max_distance=5000):
        """Tìm nhà hàng gần đây (geospatial query)"""
        return list(get_db().restaurants.find({
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                    "$maxDistance": max_distance
                }
            },
            "status": "approved"
        }))
    
    @staticmethod
    def update(rest_id, data):
        """Cập nhật thông tin nhà hàng"""
        data['updated_at'] = datetime.now()
        return get_db().restaurants.update_one(
            {"_id": ObjectId(rest_id)},
            {"$set": data}
        )
```

**Đặc điểm:**

- Sử dụng geospatial index (`2dsphere`) để tìm nhà hàng gần đây
- Hỗ trợ tìm kiếm theo vị trí địa lý (latitude, longitude)

#### 4.2.3. Class Order

Quản lý đơn hàng:

```python
class Order:
    """Class Order - Model quản lý đơn hàng"""
    
    @staticmethod
    def create(data):
        """Tạo đơn hàng mới"""
        data['created_at'] = datetime.now()
        data['status'] = 'pending'
        result = get_db().orders.insert_one(data)
        return result.inserted_id
    
    @staticmethod
    def find_by_id(order_id):
        """Tìm đơn hàng theo ID"""
        return get_db().orders.find_one({"_id": ObjectId(order_id)})
    
    @staticmethod
    def find_by_user(user_id, limit=None):
        """Tìm đơn hàng của khách hàng"""
        query = get_db().orders.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        if limit:
            query = query.limit(limit)
        return list(query)
    
    @staticmethod
    def update_status(order_id, status):
        """Cập nhật trạng thái đơn hàng"""
        return get_db().orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )
```

**Các trạng thái đơn hàng:**

- `pending`: Chờ xử lý
- `preparing`: Đang chuẩn bị
- `ready`: Sẵn sàng giao
- `delivering`: Đang giao
- `delivered`: Đã giao
- `cancelled`: Đã hủy

### 4.3. Route Layer - Xử lý Request/Response

#### 4.3.1. Route đăng nhập (`app/routes/auth.py`)

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User
from app.utils.auth import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Tìm user theo số điện thoại
        user = User.find_by_phone(phone)
        
        if user and verify_password(password, user.get('password')):
            # Lưu thông tin user vào session
            session['user_id'] = str(user['_id'])
            session['role'] = user.get('role')
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('customer.dashboard'))
        else:
            flash('Số điện thoại hoặc mật khẩu không đúng', 'danger')
    
    return render_template('auth/login.html')
```

**Giải thích:**

- Sử dụng `@auth_bp.route()` để định nghĩa route
- `request.form.get()` để lấy dữ liệu từ form
- `User.find_by_phone()` để tìm user trong database
- `session` để lưu thông tin đăng nhập
- `redirect()` và `url_for()` để điều hướng

#### 4.3.2. Route xem danh sách nhà hàng (`app/routes/customer.py`)

```python
from flask import Blueprint, render_template, request
from app.models import Restaurant
from app.utils.auth import login_required

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/restaurants')
@login_required
def restaurants():
    """Danh sách nhà hàng"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Tạo filter
    filters = {'status': 'approved'}
    if search:
        filters['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'addr': {'$regex': search, '$options': 'i'}}
        ]
    
    # Tìm kiếm trong database
    restaurants_list = list(get_db().restaurants.find(filters))
    
    return render_template('customer/restaurants.html', 
                         restaurants=restaurants_list,
                         search=search)
```

**Giải thích:**

- `@login_required`: Decorator kiểm tra đăng nhập
- `request.args.get()`: Lấy tham số từ URL (query string)
- `$regex`: Tìm kiếm theo pattern (không phân biệt hoa thường với `$options: 'i'`)
- `render_template()`: Render HTML template với dữ liệu

#### 4.3.3. Route tạo đơn hàng

```python
@customer_bp.route('/order/create', methods=['POST'])
@login_required
def create_order():
    """Tạo đơn hàng mới"""
    user = get_current_user()
    
    # Lấy dữ liệu từ form
    rest_id = request.form.get('rest_id')
    items = request.form.getlist('items')  # Danh sách món ăn
    total = request.form.get('total', type=float)
    address = request.form.get('address')
    
    # Tạo đơn hàng
    order_data = {
        'user_id': ObjectId(str(user['_id'])),
        'rest_id': ObjectId(rest_id),
        'items': items,
        'total': total,
        'address': address,
        'status': 'pending'
    }
    
    order_id = Order.create(order_data)
    
    flash('Đặt hàng thành công!', 'success')
    return redirect(url_for('customer.order_detail', order_id=order_id))
```

### 4.4. View Layer - Giao diện người dùng

#### 4.4.1. Template cơ sở (`templates/base.html`)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}FastFood Delivery{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.index') }}">FastFood</a>
            {% if session.user_id %}
                <span class="navbar-text">Xin chào, {{ session.name }}</span>
            {% endif %}
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

**Giải thích:**

- `{% block %}`: Định nghĩa block có thể override
- `{{ url_for() }}`: Tạo URL từ route name
- `{{ session.name }}`: Hiển thị dữ liệu từ session
- `get_flashed_messages()`: Lấy thông báo flash

#### 4.4.2. Template danh sách nhà hàng

```html
{% extends "base.html" %}

{% block content %}
<h2>Danh sách nhà hàng</h2>

<form method="GET" class="mb-3">
    <input type="text" name="search" value="{{ search }}" placeholder="Tìm kiếm...">
    <button type="submit">Tìm kiếm</button>
</form>

<div class="row">
    {% for restaurant in restaurants %}
    <div class="col-md-4 mb-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{{ restaurant.name }}</h5>
                <p class="card-text">{{ restaurant.addr }}</p>
                <p class="card-text">Đánh giá: {{ restaurant.rating }}/5</p>
                <a href="{{ url_for('customer.restaurant_detail', rest_id=restaurant._id) }}" 
                   class="btn btn-primary">Xem menu</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

---

## 5. Các thao tác CRUD với MongoDB

### 5.1. CREATE - Thêm dữ liệu

#### 5.1.1. Thêm một document

```python
from app.database import get_db
from datetime import datetime

# Thêm user mới
user_data = {
    'phone': '0901234567',
    'name': 'Nguyễn Văn A',
    'password': hashed_password,
    'role': 'customer',
    'created_at': datetime.now()
}

result = get_db().users.insert_one(user_data)
print(f"User ID: {result.inserted_id}")
```

#### 5.1.2. Thêm nhiều documents

```python
# Thêm nhiều menu cùng lúc
menus = [
    {'rest_id': ObjectId('...'), 'name': 'Phở Bò', 'price': 50000},
    {'rest_id': ObjectId('...'), 'name': 'Bún Bò', 'price': 45000},
    {'rest_id': ObjectId('...'), 'name': 'Bánh Mì', 'price': 20000}
]

result = get_db().menus.insert_many(menus)
print(f"Inserted {len(result.inserted_ids)} menus")
```

### 5.2. READ - Đọc dữ liệu

#### 5.2.1. Tìm một document

```python
# Tìm user theo số điện thoại
user = get_db().users.find_one({"phone": "0901234567"})

# Tìm user theo ID
user = get_db().users.find_one({"_id": ObjectId("...")})
```

#### 5.2.2. Tìm nhiều documents

```python
# Tìm tất cả nhà hàng đã được duyệt
restaurants = list(get_db().restaurants.find({"status": "approved"}))

# Tìm với điều kiện phức tạp
orders = list(get_db().orders.find({
    "user_id": ObjectId("..."),
    "status": {"$in": ["preparing", "delivering"]}
}).sort("created_at", -1))
```

#### 5.2.3. Tìm kiếm với regex

```python
# Tìm nhà hàng có tên chứa "Phở"
restaurants = list(get_db().restaurants.find({
    "name": {"$regex": "Phở", "$options": "i"}  # i = không phân biệt hoa thường
}))
```

#### 5.2.4. Tìm kiếm theo vị trí địa lý

```python
# Tìm nhà hàng gần đây (trong bán kính 5km)
restaurants = list(get_db().restaurants.find({
    "loc": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [106.6297, 10.8231]  # [longitude, latitude]
            },
            "$maxDistance": 5000  # 5km
        }
    }
}))
```

### 5.3. UPDATE - Cập nhật dữ liệu

#### 5.3.1. Cập nhật một document

```python
# Cập nhật trạng thái đơn hàng
get_db().orders.update_one(
    {"_id": ObjectId("...")},
    {"$set": {"status": "delivered", "updated_at": datetime.now()}}
)
```

#### 5.3.2. Cập nhật nhiều documents

```python
# Cập nhật tất cả menu của một nhà hàng
get_db().menus.update_many(
    {"rest_id": ObjectId("...")},
    {"$set": {"status": "active"}}
)
```

#### 5.3.3. Cập nhật với toán tử khác

```python
# Tăng giá món ăn lên 10%
get_db().menus.update_many(
    {"rest_id": ObjectId("...")},
    {"$mul": {"price": 1.1}}  # Nhân giá với 1.1
)

# Thêm món vào danh sách
get_db().orders.update_one(
    {"_id": ObjectId("...")},
    {"$push": {"items": "Phở Bò"}}  # Thêm vào mảng
)
```

### 5.4. DELETE - Xóa dữ liệu

#### 5.4.1. Xóa một document

```python
# Xóa một menu
get_db().menus.delete_one({"_id": ObjectId("...")})
```

#### 5.4.2. Xóa nhiều documents

```python
# Xóa tất cả đơn hàng đã hủy
result = get_db().orders.delete_many({"status": "cancelled"})
print(f"Deleted {result.deleted_count} orders")
```

---

## 6. Tối ưu hiệu suất với Index

### 6.1. Tại sao cần Index?

Index giúp MongoDB tìm kiếm dữ liệu nhanh hơn, tương tự như mục lục trong sách. Không có index, MongoDB phải quét toàn bộ collection (full collection scan), rất chậm với dữ liệu lớn.

### 6.2. Các loại Index trong project

#### 6.2.1. Single Field Index

```python
# Index trên trường phone (unique)
database.users.create_index("phone", unique=True)

# Index trên trường status
database.orders.create_index("status")
```

#### 6.2.2. Compound Index

```python
# Index trên nhiều trường (user_id và status)
database.orders.create_index([("user_id", 1), ("status", 1)])
```

#### 6.2.3. Geospatial Index

```python
# Index 2dsphere cho tìm kiếm theo vị trí
database.restaurants.create_index([("loc", "2dsphere")])
```

#### 6.2.4. Text Index (tìm kiếm văn bản)

```python
# Index để tìm kiếm full-text
database.restaurants.create_index([("name", "text"), ("addr", "text")])
```

### 6.3. Kiểm tra Index

```python
# Xem tất cả index của collection
indexes = get_db().users.list_indexes()
for index in indexes:
    print(index)
```

---

## 7. Xử lý lỗi và kiểm thử

### 7.1. Xử lý lỗi kết nối

```python
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

try:
    client = MongoClient(app.config['MONGODB_URI'], serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Connected successfully")
except ConnectionFailure as e:
    print(f"Connection failed: {e}")
except ServerSelectionTimeoutError as e:
    print(f"Server selection timeout: {e}")
```

### 7.2. Xử lý lỗi validation

```python
from pymongo.errors import WriteError, DuplicateKeyError

try:
    result = get_db().users.insert_one(user_data)
except DuplicateKeyError:
    flash('Số điện thoại đã tồn tại', 'danger')
except WriteError as e:
    flash(f'Lỗi khi lưu dữ liệu: {e}', 'danger')
```

### 7.3. Kiểm thử kết nối

Tạo file test: `test_connection.py`

```python
from app import create_app
from app.database import get_db

app = create_app()

with app.app_context():
    db = get_db()
    
    # Kiểm tra kết nối
    print("Collections:", db.list_collection_names())
    
    # Đếm số lượng documents
    print(f"Users: {db.users.count_documents({})}")
    print(f"Restaurants: {db.restaurants.count_documents({})}")
    print(f"Orders: {db.orders.count_documents({})}")
```

Chạy test:

```bash
python test_connection.py
```

---

## 8. Kết luận

Chương này đã trình bày cách xây dựng ứng dụng web Flask kết nối với MongoDB thông qua PyMongo, bao gồm:

1. **Cài đặt và cấu hình**: Cài đặt PyMongo, cấu hình kết nối MongoDB
2. **Kết nối database**: Sử dụng `MongoClient` để kết nối, kiểm tra kết nối
3. **Tạo Index**: Tối ưu hiệu suất với các loại index phù hợp
4. **CRUD Operations**: Thực hiện các thao tác cơ bản với database
5. **Xử lý lỗi**: Xử lý các lỗi kết nối và validation
6. **Kiến trúc ứng dụng**: Mô hình MVC với Flask

Ứng dụng minh họa này cho thấy cách một hệ thống thực tế sử dụng MongoDB để quản lý dữ liệu, từ kết nối cơ bản đến các thao tác phức tạp như tìm kiếm địa lý, tối ưu hiệu suất với index, và xử lý các trường hợp lỗi.
