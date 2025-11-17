# DANH SÁCH CÁC HÀM PYMONGO ĐÃ SỬ DỤNG TRONG PROJECT

## Tổng quan

Project này sử dụng thư viện **PyMongo** để kết nối và thao tác với MongoDB. Dưới đây là danh sách đầy đủ các hàm PyMongo đã được sử dụng trong project.

---

## 1. Kết nối và Quản lý Database

### 1.1. `MongoClient()`
**File sử dụng:** `app/database.py`

**Mục đích:** Tạo kết nối đến MongoDB server

**Ví dụ:**
```python
from pymongo import MongoClient

client = MongoClient(app.config['MONGODB_URI'])
```

**Chức năng:** Khởi tạo client để kết nối với MongoDB server

---

### 1.2. `client[database_name]`
**File sử dụng:** `app/database.py`

**Mục đích:** Chọn database cụ thể

**Ví dụ:**
```python
db = client[app.config['MONGODB_DB']]
# db = client['fastfood']
```

**Chức năng:** Lấy instance của database để thao tác

---

### 1.3. `client.admin.command('ping')`
**File sử dụng:** `app/database.py`

**Mục đích:** Kiểm tra kết nối MongoDB có hoạt động không

**Ví dụ:**
```python
client.admin.command('ping')
```

**Chức năng:** Gửi lệnh ping đến MongoDB để kiểm tra kết nối

---

## 2. Tìm kiếm Documents (Query)

### 2.1. `collection.find(query)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Tìm nhiều documents theo điều kiện

**Ví dụ:**
```python
# Tìm tất cả user có role là customer
users = get_db().users.find({"role": "customer"})

# Tìm đơn hàng của user
orders = get_db().orders.find({"user_id": ObjectId(user_id)})

# Tìm với điều kiện phức tạp
orders = get_db().orders.find({
    "shipper_id": None,
    "status": {"$in": ["pending", "preparing"]}
})
```

**Chức năng:** Trả về cursor chứa tất cả documents khớp với query

**Sử dụng trong:**
- `User.find_by_role()` - Tìm user theo role
- `Restaurant.find_all()` - Tìm tất cả restaurant
- `Restaurant.find_by_owner()` - Tìm restaurant theo owner
- `Restaurant.find_nearby()` - Tìm restaurant gần vị trí
- `Menu.find_by_restaurant()` - Tìm menu theo restaurant
- `Order.find_by_user()` - Tìm đơn hàng theo user
- `Order.find_available()` - Tìm đơn hàng chưa có shipper
- `Review.find_by_restaurant()` - Tìm đánh giá theo restaurant
- `Review.find_by_shipper()` - Tìm đánh giá theo shipper
- `Review.find_by_menu()` - Tìm đánh giá theo menu
- Các route trong `admin.py`, `customer.py`, `shipper.py`, `restaurant.py`

---

### 2.2. `collection.find_one(query)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Tìm một document duy nhất theo điều kiện

**Ví dụ:**
```python
# Tìm user theo số điện thoại
user = get_db().users.find_one({"phone": phone})

# Tìm user theo ID
user = get_db().users.find_one({"_id": ObjectId(user_id)})

# Tìm restaurant theo ID
restaurant = get_db().restaurants.find_one({"_id": ObjectId(rest_id)})

# Tìm đánh giá theo order_id
review = get_db().reviews.find_one({"order_id": ObjectId(order_id)})
```

**Chức năng:** Trả về document đầu tiên khớp với query, hoặc None nếu không tìm thấy

**Sử dụng trong:**
- `User.find_by_phone()` - Tìm user theo phone
- `User.find_by_id()` - Tìm user theo ID
- `User.get_cart()` - Lấy giỏ hàng của user
- `Restaurant.find_by_id()` - Tìm restaurant theo ID
- `Menu.find_by_id()` - Tìm menu theo ID
- `Order.find_by_id()` - Tìm order theo ID
- `Payment.find_by_order()` - Tìm payment theo order
- `Review.find_by_order()` - Tìm review theo order
- Các route để tìm kiếm document cụ thể

---

### 2.3. `collection.count_documents(query)`
**File sử dụng:** `app/routes/admin.py`

**Mục đích:** Đếm số lượng documents khớp với điều kiện

**Ví dụ:**
```python
# Đếm tổng số users
total_users = db.users.count_documents({})

# Đếm số đơn hàng đang chờ
pending_orders = db.orders.count_documents({'status': 'pending'})

# Đếm số shipper đang chờ duyệt
pending_shippers = db.users.count_documents({'role': 'shipper', 'status': 'pending'})

# Đếm số đánh giá 0 sao của shipper
zero_star_count = db.reviews.count_documents({
    "shipper_id": ObjectId(shipper_id),
    "driver_rating": 0
})
```

**Chức năng:** Trả về số lượng documents khớp với query

**Sử dụng trong:**
- `admin.dashboard()` - Thống kê tổng quan
- `Review.count_zero_star_reviews()` - Đếm đánh giá 0 sao

---

## 3. Thêm Documents (Insert)

### 3.1. `collection.insert_one(data)`
**File sử dụng:** `app/models.py`

**Mục đích:** Chèn một document mới vào collection

**Ví dụ:**
```python
# Tạo user mới
result = get_db().users.insert_one(data)
user_id = result.inserted_id

# Tạo restaurant mới
result = get_db().restaurants.insert_one(data)
restaurant_id = result.inserted_id

# Tạo menu mới
result = get_db().menus.insert_one(data)
menu_id = result.inserted_id

# Tạo order mới
result = get_db().orders.insert_one(data)
order_id = result.inserted_id

# Tạo payment mới
result = get_db().payments.insert_one(data)
payment_id = result.inserted_id

# Tạo review mới
result = get_db().reviews.insert_one(data)
review_id = result.inserted_id
```

**Chức năng:** Chèn document mới và trả về kết quả chứa `inserted_id`

**Sử dụng trong:**
- `User.create()` - Tạo user mới
- `Restaurant.create()` - Tạo restaurant mới
- `Menu.create()` - Tạo menu mới
- `Order.create()` - Tạo order mới
- `Payment.create()` - Tạo payment mới
- `Review.create()` - Tạo review mới

---

## 4. Cập nhật Documents (Update)

### 4.1. `collection.update_one(filter, update)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Cập nhật một document theo điều kiện

**Ví dụ:**
```python
# Cập nhật thông tin user
get_db().users.update_one(
    {"_id": ObjectId(user_id)},
    {"$set": data}
)

# Cập nhật giỏ hàng
get_db().users.update_one(
    {"_id": ObjectId(user_id)},
    {"$set": {"cart": cart, "cart_updated_at": datetime.now()}}
)

# Cập nhật trạng thái đơn hàng
get_db().orders.update_one(
    {"_id": ObjectId(order_id)},
    {"$set": {"status": status, "updated_at": datetime.now()}}
)

# Cập nhật trạng thái thanh toán
get_db().payments.update_one(
    {"_id": ObjectId(payment_id)},
    {"$set": {"status": status, "updated_at": datetime.now()}}
)
```

**Chức năng:** Cập nhật document đầu tiên khớp với filter

**Sử dụng trong:**
- `User.update()` - Cập nhật thông tin user
- `User.save_cart()` - Lưu giỏ hàng
- `Restaurant.update()` - Cập nhật restaurant
- `Menu.update()` - Cập nhật menu
- `Order.update_status()` - Cập nhật trạng thái order
- `Payment.update_status()` - Cập nhật trạng thái payment
- Các route cập nhật dữ liệu

---

## 5. Xóa Documents (Delete)

### 5.1. `collection.delete_one(filter)`
**File sử dụng:** `app/models.py`

**Mục đích:** Xóa một document theo điều kiện

**Ví dụ:**
```python
# Xóa menu
get_db().menus.delete_one({"_id": ObjectId(menu_id)})
```

**Chức năng:** Xóa document đầu tiên khớp với filter

**Sử dụng trong:**
- `Menu.delete()` - Xóa menu

---

## 6. Quản lý Index

### 6.1. `collection.create_index(keys, options)`
**File sử dụng:** `app/database.py`

**Mục đích:** Tạo index để tối ưu hiệu suất truy vấn

**Ví dụ:**
```python
# Tạo index đơn giản
database.users.create_index("role")
database.users.create_index("status")

# Tạo index unique
database.users.create_index("phone", unique=True)

# Tạo index địa lý (geospatial)
database.restaurants.create_index([("loc", "2dsphere")])

# Tạo index với tên tùy chỉnh
database.reviews.create_index("order_id", unique=True, name="order_id_unique")

# Tạo index cho nested field
database.reviews.create_index("menu_ratings.menu_id")
```

**Chức năng:** Tạo index trên một hoặc nhiều trường để tăng tốc độ truy vấn

**Sử dụng trong:**
- `create_indexes()` - Tạo tất cả index khi khởi động app

---

### 6.2. `collection.drop_index(index_name)`
**File sử dụng:** `app/database.py`

**Mục đích:** Xóa index đã tồn tại

**Ví dụ:**
```python
# Xóa index cũ trước khi tạo lại
database.reviews.drop_index("order_id_1")
```

**Chức năng:** Xóa index theo tên

**Sử dụng trong:**
- `create_indexes()` - Xóa index cũ trước khi tạo lại với cấu hình mới

---

## 7. Xử lý Cursor (Kết quả truy vấn)

### 7.1. `cursor.sort(field, direction)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Sắp xếp kết quả truy vấn

**Ví dụ:**
```python
# Sắp xếp theo thời gian tạo, mới nhất trước
cursor = get_db().orders.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)

# Sắp xếp theo updated_at, mới nhất trước
recent_orders = list(db.orders.find().sort('updated_at', -1).limit(10))
```

**Chức năng:** Sắp xếp cursor theo trường và hướng (1 = tăng dần, -1 = giảm dần)

**Sử dụng trong:**
- `Order.find_by_user()` - Sắp xếp đơn hàng theo thời gian
- `Review.find_by_restaurant()` - Sắp xếp đánh giá theo thời gian
- `Review.find_by_shipper()` - Sắp xếp đánh giá theo thời gian
- `admin.dashboard()` - Lấy đơn hàng gần đây

---

### 7.2. `cursor.limit(number)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Giới hạn số lượng documents trả về

**Ví dụ:**
```python
# Lấy tối đa 10 đơn hàng
cursor = get_db().orders.find({"user_id": ObjectId(user_id)}).limit(10)

# Lấy 10 đơn hàng gần đây nhất
recent_orders = list(db.orders.find().sort('created_at', -1).limit(10))
```

**Chức năng:** Giới hạn số lượng documents trong cursor

**Sử dụng trong:**
- `Restaurant.find_all()` - Phân trang
- `Order.find_by_user()` - Giới hạn số đơn hàng
- `admin.dashboard()` - Lấy đơn hàng gần đây

---

### 7.3. `cursor.skip(number)`
**File sử dụng:** `app/models.py`

**Mục đích:** Bỏ qua số lượng documents đầu tiên (dùng cho phân trang)

**Ví dụ:**
```python
# Bỏ qua 20 documents đầu tiên (trang 2, mỗi trang 20 items)
cursor = get_db().restaurants.find(query).skip(20).limit(20)
```

**Chức năng:** Bỏ qua số lượng documents trong cursor

**Sử dụng trong:**
- `Restaurant.find_all()` - Phân trang

---

### 7.4. `list(cursor)`
**File sử dụng:** `app/models.py`, `app/routes/*.py`

**Mục đích:** Chuyển cursor thành list Python

**Ví dụ:**
```python
# Chuyển cursor thành list
users = list(get_db().users.find({"role": "customer"}))
orders = list(get_db().orders.find({"user_id": ObjectId(user_id)}))
```

**Chức năng:** Chuyển đổi cursor (lazy evaluation) thành list (eager evaluation)

**Sử dụng trong:**
- Tất cả các hàm trả về list documents

---

## 8. Toán tử MongoDB (MongoDB Operators)

### 8.1. `$set`
**Mục đích:** Cập nhật giá trị của trường

**Ví dụ:**
```python
{"$set": {"status": "active", "updated_at": datetime.now()}}
{"$set": {"cart": cart, "cart_updated_at": datetime.now()}}
{"$set": data}  # Cập nhật nhiều trường
```

**Sử dụng trong:** Tất cả các thao tác `update_one()`

---

### 8.2. `$in`
**Mục đích:** Tìm documents có giá trị trong danh sách

**Ví dụ:**
```python
# Tìm đơn hàng có status là pending hoặc preparing
{"status": {"$in": ["pending", "preparing"]}}

# Tìm đơn hàng đang preparing hoặc delivering
{'status': {'$in': ['preparing', 'delivering']}}
```

**Sử dụng trong:**
- `Order.find_available()` - Tìm đơn hàng có sẵn
- `customer.dashboard()` - Tìm đơn hàng đang xử lý

---

### 8.3. `$near` (Geospatial)
**Mục đích:** Tìm documents gần một vị trí địa lý

**Ví dụ:**
```python
{
    "loc": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [lng, lat]  # [kinh độ, vĩ độ]
            },
            "$maxDistance": 5000  # 5km
        }
    },
    "status": "approved"
}
```

**Sử dụng trong:**
- `Restaurant.find_nearby()` - Tìm nhà hàng gần vị trí

---

### 8.4. `$or`
**Mục đích:** Tìm documents khớp với một trong các điều kiện

**Ví dụ:**
```python
{
    "$or": [
        {'name': {'$regex': search, '$options': 'i'}},
        {'phone': {'$regex': search, '$options': 'i'}}
    ]
}
```

**Sử dụng trong:**
- `admin.users()` - Tìm kiếm user theo tên hoặc số điện thoại

---

### 8.5. `$regex`
**Mục đích:** Tìm kiếm theo pattern (regular expression)

**Ví dụ:**
```python
{'name': {'$regex': search, '$options': 'i'}}
# $options: 'i' = case insensitive (không phân biệt hoa thường)
```

**Sử dụng trong:**
- `admin.users()` - Tìm kiếm user

---

## 9. ObjectId

### 9.1. `ObjectId(string_id)`
**File sử dụng:** Tất cả các file models và routes

**Mục đích:** Chuyển đổi string ID sang ObjectId của MongoDB

**Ví dụ:**
```python
from bson import ObjectId

# Chuyển string sang ObjectId
user_id = ObjectId("507f1f77bcf86cd799439011")

# Sử dụng trong query
user = get_db().users.find_one({"_id": ObjectId(user_id)})
```

**Chức năng:** Chuyển đổi string ID thành ObjectId để query MongoDB

**Sử dụng trong:** Tất cả các query sử dụng `_id`

---

## 10. Tóm tắt các hàm đã sử dụng

| Hàm PyMongo | Số lần sử dụng | Mục đích |
|-------------|----------------|----------|
| `MongoClient()` | 1 | Tạo kết nối MongoDB |
| `client[database]` | 1 | Chọn database |
| `client.admin.command()` | 1 | Kiểm tra kết nối |
| `collection.find()` | ~30+ | Tìm nhiều documents |
| `collection.find_one()` | ~20+ | Tìm một document |
| `collection.insert_one()` | 6 | Tạo document mới |
| `collection.update_one()` | ~15+ | Cập nhật document |
| `collection.delete_one()` | 1 | Xóa document |
| `collection.count_documents()` | ~10+ | Đếm documents |
| `collection.create_index()` | 20+ | Tạo index |
| `collection.drop_index()` | 1 | Xóa index |
| `cursor.sort()` | ~10+ | Sắp xếp kết quả |
| `cursor.limit()` | ~5+ | Giới hạn số lượng |
| `cursor.skip()` | 1 | Bỏ qua documents |
| `list()` | ~20+ | Chuyển cursor thành list |

---

## 11. Các toán tử MongoDB đã sử dụng

| Toán tử | Mục đích | Ví dụ |
|--------|----------|-------|
| `$set` | Cập nhật trường | `{"$set": {"status": "active"}}` |
| `$in` | Tìm trong danh sách | `{"status": {"$in": ["pending", "preparing"]}}` |
| `$near` | Tìm kiếm địa lý | Tìm nhà hàng gần vị trí |
| `$geometry` | Định nghĩa điểm địa lý | GeoJSON Point |
| `$maxDistance` | Khoảng cách tối đa | 5000 (mét) |
| `$or` | Điều kiện OR | Tìm theo tên HOẶC số điện thoại |
| `$regex` | Tìm kiếm pattern | Tìm kiếm không phân biệt hoa thường |

---

## 12. Các hàm CHƯA sử dụng (có thể bổ sung)

- `collection.insert_many()` - Chèn nhiều documents cùng lúc
- `collection.update_many()` - Cập nhật nhiều documents
- `collection.delete_many()` - Xóa nhiều documents
- `collection.replace_one()` - Thay thế document
- `collection.find_one_and_update()` - Tìm và cập nhật
- `collection.find_one_and_delete()` - Tìm và xóa
- `collection.aggregate()` - Aggregation pipeline
- `collection.distinct()` - Lấy giá trị duy nhất
- `collection.bulk_write()` - Thao tác hàng loạt
- `collection.create_indexes()` - Tạo nhiều index cùng lúc

---

## 13. Kết luận

Project này đã sử dụng các hàm PyMongo cơ bản và quan trọng nhất:

1. **Kết nối:** `MongoClient()`, `client[database]`, `command()`
2. **Tìm kiếm:** `find()`, `find_one()`, `count_documents()`
3. **Thêm:** `insert_one()`
4. **Cập nhật:** `update_one()` với toán tử `$set`
5. **Xóa:** `delete_one()`
6. **Index:** `create_index()`, `drop_index()`
7. **Cursor:** `sort()`, `limit()`, `skip()`, `list()`
8. **Toán tử:** `$set`, `$in`, `$near`, `$or`, `$regex`

Đây là các hàm đủ để xây dựng một ứng dụng web hoàn chỉnh với MongoDB!

