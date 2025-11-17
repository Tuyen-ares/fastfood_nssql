# MongoDB Relationships - Giải Thích Chi Tiết

## 📌 Câu Hỏi: MongoDB Có Tự Động Nối Collections Không?

### ❌ **TRẢ LỜI: KHÔNG!**

MongoDB **KHÔNG** tự động nối (join) collections như SQL databases. MongoDB cũng **KHÔNG** có foreign key constraints tự động.

---

## 🔍 So Sánh MongoDB vs SQL

### SQL Database (MySQL, PostgreSQL):
```sql
-- SQL có FOREIGN KEY constraint tự động
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id)  -- Ràng buộc tự động
);

-- SQL tự động JOIN khi query
SELECT o.*, u.name, u.phone 
FROM orders o
JOIN users u ON o.user_id = u.id;  -- Tự động join
```

### MongoDB (NoSQL):
```javascript
// MongoDB KHÔNG có foreign key constraint
db.orders.insertOne({
    user_id: ObjectId("..."),  // Chỉ là reference, KHÔNG có ràng buộc
    total: 100000
});

// MongoDB KHÔNG tự động join
// Phải query 2 lần riêng biệt:
let order = db.orders.findOne({_id: ObjectId("...")});
let user = db.users.findOne({_id: order.user_id});  // Phải tự query
```

---

## 🎯 Vậy "Dây Nối" Trong Sơ Đồ Là Gì?

Các **"dây nối"** trong sơ đồ database chỉ là **mối quan hệ logic (logical relationships)**, **KHÔNG phải ràng buộc vật lý** như SQL.

### Ví dụ trong project:

```
orders.user_id → users._id
orders.rest_id → restaurants._id
orders.shipper_id → users._id
payments.order_id → orders._id
reviews.order_id → orders._id
```

**Những "dây nối" này có nghĩa là:**
- ✅ **Lưu trữ ObjectId** của document khác (reference)
- ✅ **Quy ước logic** để ứng dụng biết cách query
- ❌ **KHÔNG** có ràng buộc tự động
- ❌ **KHÔNG** tự động kiểm tra document có tồn tại không
- ❌ **KHÔNG** tự động xóa khi document cha bị xóa

---

## 💻 Cách Project Này Xử Lý Relationships

### Ví dụ 1: Lấy thông tin đơn hàng kèm nhà hàng và thanh toán

**File:** `app/routes/customer.py` (dòng 407-469)

```python
@customer_bp.route('/order/<order_id>')
def order_detail(order_id):
    # BƯỚC 1: Query order (1 lần query)
    order = Order.find_by_id(order_id)
    # order chứa: user_id, rest_id, shipper_id (chỉ là ObjectId)
    
    # BƯỚC 2: Query restaurant (query riêng, dựa vào rest_id trong order)
    restaurant = Restaurant.find_by_id(str(order['rest_id']))
    
    # BƯỚC 3: Query payment (query riêng, dựa vào order_id)
    payment = Payment.find_by_order(order_id)
    
    # BƯỚC 4: Query review (query riêng)
    review = Review.find_by_order(order_id)
    
    # BƯỚC 5: Query shipper (query riêng, nếu có)
    shipper = None
    if order.get('shipper_id'):
        shipper = User.find_by_id(str(order['shipper_id']))
    
    # BƯỚC 6: Query menu items (query nhiều lần trong vòng lặp)
    menu_items = []
    for item in order.get('items', []):
        menu = Menu.find_by_id(str(item['menu_id']))  # Query từng món
        menu_items.append({'menu': menu, 'quantity': item['quantity']})
    
    return render_template('customer/order_detail.html',
                         order=order,
                         restaurant=restaurant,
                         payment=payment,
                         shipper=shipper,
                         review=review,
                         menu_items=menu_items)
```

**Tổng cộng: 5-10 lần query riêng biệt!** (SQL chỉ cần 1 lần JOIN)

---

## 🔧 Các Cách Xử Lý Relationships Trong MongoDB

### 1. **Reference (Tham Chiếu)** - Cách project này dùng

**Ưu điểm:**
- Dữ liệu không trùng lặp
- Dễ cập nhật (chỉ cần sửa 1 nơi)
- Phù hợp với dữ liệu thay đổi thường xuyên

**Nhược điểm:**
- Phải query nhiều lần
- Chậm hơn nếu cần nhiều dữ liệu liên quan

**Ví dụ:**
```python
# Order document
{
    "_id": ObjectId("..."),
    "user_id": ObjectId("user123"),  # Reference đến users
    "rest_id": ObjectId("rest456"),   # Reference đến restaurants
    "total": 100000
}

# Phải query riêng để lấy thông tin user và restaurant
user = User.find_by_id("user123")
restaurant = Restaurant.find_by_id("rest456")
```

### 2. **Embedding (Nhúng)** - Không dùng trong project này

**Ưu điểm:**
- Query nhanh (chỉ cần 1 lần)
- Dữ liệu liên quan ở cùng 1 document

**Nhược điểm:**
- Dữ liệu trùng lặp
- Document có thể quá lớn (giới hạn 16MB)
- Khó cập nhật (phải sửa nhiều nơi)

**Ví dụ (KHÔNG dùng trong project):**
```python
# Order document với embedded user info
{
    "_id": ObjectId("..."),
    "user": {  # Nhúng thông tin user vào order
        "name": "Nguyễn Văn A",
        "phone": "0123456789"
    },
    "restaurant": {  # Nhúng thông tin restaurant
        "name": "Burger King",
        "address": "123 Đường ABC"
    },
    "total": 100000
}
```

### 3. **Aggregation Pipeline** - Có thể dùng nhưng project này chưa dùng

**Ưu điểm:**
- Có thể "join" nhiều collections trong 1 query
- Linh hoạt, mạnh mẽ

**Nhược điểm:**
- Phức tạp hơn
- Có thể chậm với dữ liệu lớn

**Ví dụ (KHÔNG dùng trong project):**
```python
# Sử dụng $lookup để "join" collections
pipeline = [
    {"$match": {"_id": ObjectId(order_id)}},
    {"$lookup": {
        "from": "users",
        "localField": "user_id",
        "foreignField": "_id",
        "as": "user_info"
    }},
    {"$lookup": {
        "from": "restaurants",
        "localField": "rest_id",
        "foreignField": "_id",
        "as": "restaurant_info"
    }}
]
order_with_details = list(db.orders.aggregate(pipeline))
```

---

## 🛡️ Bảo Vệ Tính Toàn Vẹn Dữ Liệu

Vì MongoDB **KHÔNG** có foreign key constraints, ứng dụng phải **tự kiểm tra**:

### Ví dụ trong project:

**File:** `app/routes/customer.py` - Tạo order

```python
# Khi tạo order, phải tự kiểm tra:
rest_id = request.form.get('rest_id')
restaurant = Restaurant.find_by_id(rest_id)  # Kiểm tra restaurant có tồn tại không

if not restaurant:
    flash('Nhà hàng không tồn tại', 'danger')
    return redirect(url_for('customer.cart'))

# Nếu restaurant tồn tại, mới tạo order
order_data = {
    'user_id': str(user['_id']),
    'rest_id': rest_id,  # Chỉ lưu ObjectId, không có ràng buộc
    'total': total
}
Order.create(order_data)
```

**Vấn đề:** Nếu sau đó xóa restaurant, các orders vẫn còn `rest_id` trỏ đến restaurant đã xóa!

**Giải pháp:** 
- ✅ Kiểm tra trước khi xóa (xem có orders nào đang dùng không)
- ✅ Hoặc dùng "soft delete" (đánh dấu `status: 'deleted'` thay vì xóa thật)

---

## 📊 Index và Performance

Mặc dù MongoDB không có foreign key, nhưng vẫn tạo **index** cho các trường reference để tăng tốc query:

**File:** `app/database.py`

```python
# Tạo index cho user_id trong orders (để tìm orders của user nhanh hơn)
database.orders.create_index("user_id")

# Tạo index cho rest_id trong orders (để tìm orders của restaurant nhanh hơn)
database.orders.create_index("rest_id")

# Tạo index cho order_id trong payments (để tìm payment của order nhanh hơn)
database.payments.create_index("order_id")
```

**Lưu ý:** Index chỉ giúp **tìm kiếm nhanh hơn**, **KHÔNG** tạo ràng buộc!

---

## 🎯 Tóm Tắt

| Tính Năng | SQL Database | MongoDB |
|-----------|--------------|---------|
| **Foreign Key Constraint** | ✅ Có tự động | ❌ Không có |
| **Tự động JOIN** | ✅ Có (JOIN) | ❌ Không (phải query nhiều lần) |
| **Ràng buộc dữ liệu** | ✅ Tự động | ❌ Phải tự code |
| **"Dây nối" trong sơ đồ** | Ràng buộc vật lý | Chỉ là reference logic |
| **Cách xử lý** | 1 query với JOIN | Nhiều query riêng biệt |

---

## 💡 Kết Luận

1. **MongoDB KHÔNG tự động nối collections** - Phải tự query nhiều lần
2. **MongoDB KHÔNG có foreign key** - Phải tự kiểm tra tính toàn vẹn
3. **"Dây nối" trong sơ đồ** chỉ là **quy ước logic**, không phải ràng buộc vật lý
4. **Index** chỉ giúp tăng tốc query, không tạo ràng buộc
5. **Ứng dụng phải tự quản lý** tất cả relationships và tính toàn vẹn dữ liệu

---

## 📝 Ví Dụ Thực Tế Từ Project

Khi xem chi tiết đơn hàng, code phải:

```python
# 1. Query order
order = Order.find_by_id(order_id)  # Query 1

# 2. Query restaurant (dựa vào rest_id trong order)
restaurant = Restaurant.find_by_id(str(order['rest_id']))  # Query 2

# 3. Query payment (dựa vào order_id)
payment = Payment.find_by_order(order_id)  # Query 3

# 4. Query review (dựa vào order_id)
review = Review.find_by_order(order_id)  # Query 4

# 5. Query shipper (dựa vào shipper_id trong order)
if order.get('shipper_id'):
    shipper = User.find_by_id(str(order['shipper_id']))  # Query 5

# 6. Query từng menu item (trong vòng lặp)
for item in order.get('items', []):
    menu = Menu.find_by_id(str(item['menu_id']))  # Query 6, 7, 8...
```

**Tổng cộng: 5-10 queries riêng biệt!**

Trong SQL, chỉ cần:
```sql
SELECT * FROM orders o
LEFT JOIN restaurants r ON o.rest_id = r.id
LEFT JOIN payments p ON p.order_id = o.id
LEFT JOIN reviews rev ON rev.order_id = o.id
LEFT JOIN users u ON o.shipper_id = u.id
WHERE o.id = ?
-- Chỉ 1 query duy nhất!
```

