# HƯỚNG DẪN ĐỌC HIỂU PROJECT - HỆ THỐNG GIAO THỨC ĂN NHANH

## Mục lục

1. [Tổng quan cấu trúc project](#1-tổng-quan-cấu-trúc-project)
2. [Thứ tự đọc hiểu từ đầu đến cuối](#2-thứ-tự-đọc-hiểu-từ-đầu-đến-cuối)
3. [Chi tiết từng folder và file](#3-chi-tiết-từng-folder-và-file)

---

## 1. Tổng quan cấu trúc project

```
DoAn/
├── app/                    # Thư mục chính chứa code ứng dụng
├── templates/              # Thư mục chứa file HTML (giao diện)
├── static/                 # Thư mục chứa CSS, JS, hình ảnh
├── doc/                    # Thư mục chứa tài liệu
├── venv/                   # Thư mục virtual environment (không cần đọc)
├── run.py                  # File khởi chạy ứng dụng
├── requirements.txt         # Danh sách thư viện cần cài đặt
└── README.md               # Hướng dẫn tổng quan
```

---

## 2. Thứ tự đọc hiểu từ đầu đến cuối

### BƯỚC 1: Đọc file cấu hình và khởi tạo (Nền tảng)**

#### 1.1. `requirements.txt`

**Mục đích:** Liệt kê tất cả thư viện Python cần thiết cho project

- **Khi nào đọc:** Đầu tiên, để biết project sử dụng công nghệ gì
- **Nội dung:**
  - Flask: Framework web
  - Flask-Bcrypt: Mã hóa mật khẩu
  - pymongo: Kết nối MongoDB
  - Werkzeug: Công cụ hỗ trợ Flask

#### 1.2. `README.md`

**Mục đích:** Hướng dẫn tổng quan về project, cách cài đặt và chạy

- **Khi nào đọc:** Sau khi đọc requirements.txt
- **Nội dung:** Cấu trúc project, hướng dẫn cài đặt, tài khoản mặc định

---

### BƯỚC 2: Đọc file cấu hình ứng dụng (Cấu hình)**

#### 2.1. `app/config.py`

**Mục đích:** Chứa tất cả cấu hình của ứng dụng

- **Khi nào đọc:** Sau khi hiểu tổng quan project
- **Nội dung chính:**
  - Cấu hình MongoDB (host, port, database name, URI)
  - Cấu hình Flask (SECRET_KEY, session)
  - Cấu hình upload file (thư mục, kích thước tối đa)
  - Cấu hình VnPay (thanh toán online)
- **Tại sao quan trọng:** Đây là nơi định nghĩa tất cả thông số kết nối và cấu hình

#### 2.2. `app/database.py`

**Mục đích:** File kết nối MongoDB - **FILE QUAN TRỌNG NHẤT**

- **Khi nào đọc:** Ngay sau config.py
- **Nội dung chính:**
  - Hàm `init_db()`: Khởi tạo kết nối MongoDB
  - Hàm `create_indexes()`: Tạo index để tối ưu hiệu suất
  - Hàm `get_db()`: Lấy database instance để sử dụng
- **Tại sao quan trọng:** Đây là cầu nối giữa ứng dụng và database MongoDB

---

### BƯỚC 3: Đọc file khởi tạo ứng dụng (Khởi động)**

#### 3.1. `app/__init__.py`

**Mục đích:** Khởi tạo Flask application và đăng ký các module

- **Khi nào đọc:** Sau khi hiểu database.py
- **Nội dung chính:**
  - Hàm `create_app()`: Tạo Flask app
  - Khởi tạo Bcrypt (mã hóa mật khẩu)
  - Gọi `init_db()` để kết nối MongoDB
  - Đăng ký các blueprint (routes)
- **Tại sao quan trọng:** Đây là điểm khởi đầu của ứng dụng, nơi kết nối tất cả các module

#### 3.2. `run.py`

**Mục đích:** File khởi chạy ứng dụng (entry point)

- **Khi nào đọc:** Sau khi hiểu **init**.py
- **Nội dung chính:**
  - Import và tạo Flask app
  - Chạy ứng dụng trên port 5000
- **Tại sao quan trọng:** Đây là file chạy để khởi động server

---

### BƯỚC 4: Đọc file Models (Dữ liệu)**

#### 4.1. `app/models.py`

**Mục đích:** Định nghĩa các class model để thao tác với database

- **Khi nào đọc:** Sau khi hiểu cách kết nối database
- **Nội dung chính:**
  - **Class User:** Quản lý người dùng (tìm, tạo, cập nhật, lưu giỏ hàng)
  - **Class Restaurant:** Quản lý nhà hàng (tìm, tạo, cập nhật, tìm gần đây)
  - **Class Menu:** Quản lý món ăn (tìm, tạo, cập nhật, xóa)
  - **Class Order:** Quản lý đơn hàng (tìm, tạo, cập nhật trạng thái)
  - **Class Payment:** Quản lý thanh toán (tìm, tạo, cập nhật)
  - **Class Review:** Quản lý đánh giá (tạo, tìm, tính điểm trung bình)
- **Tại sao quan trọng:** Đây là lớp trung gian giữa routes và database, chứa tất cả logic thao tác dữ liệu

---

### BƯỚC 5: Đọc file Utilities (Tiện ích)**

#### 5.1. `app/utils/auth.py`

**Mục đích:** Các hàm hỗ trợ xác thực người dùng

- **Khi nào đọc:** Trước khi đọc routes
- **Nội dung chính:**
  - Hàm `login_required`: Decorator kiểm tra đăng nhập
  - Hàm `role_required`: Decorator kiểm tra quyền truy cập
  - Hàm `get_current_user`: Lấy thông tin user hiện tại
- **Tại sao quan trọng:** Đảm bảo bảo mật, chỉ user đã đăng nhập và có quyền mới truy cập được

#### 5.2. `app/utils/vnpay.py`

**Mục đích:** Xử lý tích hợp thanh toán VnPay

- **Khi nào đọc:** Khi cần hiểu chức năng thanh toán
- **Nội dung chính:**
  - Tạo URL thanh toán VnPay
  - Xác thực kết quả thanh toán
  - Xử lý callback từ VnPay
- **Tại sao quan trọng:** Xử lý thanh toán online cho đơn hàng

#### 5.3. `app/utils/helpers.py`

**Mục đích:** Các hàm tiện ích hỗ trợ

- **Khi nào đọc:** Khi cần hiểu các hàm helper
- **Nội dung chính:** Các hàm tiện ích dùng chung trong project

---

### BƯỚC 6: Đọc file Routes (Logic xử lý)**

Routes là nơi xử lý request từ người dùng và trả về response. Đọc theo thứ tự:

#### 6.1. `app/routes/main.py`

**Mục đích:** Xử lý trang chủ và các route công khai

- **Khi nào đọc:** Đầu tiên trong routes
- **Nội dung chính:**
  - Route `/`: Trang chủ hiển thị món ăn theo danh mục
  - Hàm `get_menu_image()`: Lấy hình ảnh cho món ăn
- **Tại sao quan trọng:** Đây là trang đầu tiên người dùng thấy

#### 6.2. `app/routes/auth.py`

**Mục đích:** Xử lý đăng nhập và đăng ký

- **Khi nào đọc:** Sau main.py
- **Nội dung chính:**
  - Route `/login`: Xử lý đăng nhập
  - Route `/register`: Xử lý đăng ký (chỉ customer và restaurant_owner)
  - Route `/logout`: Đăng xuất
- **Tại sao quan trọng:** Quản lý xác thực người dùng

#### 6.3. `app/routes/customer.py`

**Mục đích:** Xử lý tất cả chức năng của khách hàng

- **Khi nào đọc:** Sau auth.py
- **Nội dung chính:**
  - Dashboard: Trang chủ khách hàng
  - Restaurants: Danh sách nhà hàng, xem chi tiết
  - Cart: Giỏ hàng, thêm/xóa/cập nhật số lượng
  - Checkout: Thanh toán đơn hàng
  - Orders: Xem lịch sử đơn hàng, chi tiết đơn hàng
  - Reviews: Xem và tạo đánh giá
  - Payment: Xử lý thanh toán VnPay
- **Tại sao quan trọng:** Chứa toàn bộ logic nghiệp vụ của khách hàng

#### 6.4. `app/routes/restaurant.py`

**Mục đích:** Xử lý chức năng của chủ nhà hàng

- **Khi nào đọc:** Sau customer.py
- **Nội dung chính:**
  - Register: Đăng ký nhà hàng mới
  - Dashboard: Trang quản lý nhà hàng
  - Menus: Quản lý món ăn (thêm, sửa, xóa)
  - Orders: Xem và cập nhật đơn hàng
  - Reviews: Xem đánh giá nhận được
- **Tại sao quan trọng:** Quản lý nhà hàng và menu

#### 6.5. `app/routes/shipper.py`

**Mục đích:** Xử lý chức năng của tài xế (shipper)

- **Khi nào đọc:** Sau restaurant.py
- **Nội dung chính:**
  - Dashboard: Trang chủ shipper
  - Orders: Xem đơn hàng có sẵn, nhận đơn, cập nhật trạng thái giao hàng
  - Stats: Thống kê thu nhập
  - Reviews: Xem đánh giá của khách hàng
- **Tại sao quan trọng:** Quản lý giao hàng

#### 6.6. `app/routes/admin.py`

**Mục đích:** Xử lý chức năng của admin

- **Khi nào đọc:** Cuối cùng trong routes
- **Nội dung chính:**
  - Dashboard: Trang tổng quan với thống kê
  - Users: Quản lý người dùng, duyệt tài khoản
  - Restaurants: Quản lý nhà hàng, duyệt nhà hàng
  - Shippers: Quản lý tài xế, duyệt tài xế
  - Restaurant Owners: Xem mapping chủ nhà hàng - nhà hàng
  - Orders: Quản lý đơn hàng
- **Tại sao quan trọng:** Quản trị toàn bộ hệ thống

---

### BƯỚC 7: Đọc Templates (Giao diện)**

Templates là file HTML hiển thị giao diện cho người dùng. Đọc theo thứ tự:

#### 7.1. `templates/base.html`

**Mục đích:** Template cơ sở, chứa layout chung (header, sidebar, footer)

- **Khi nào đọc:** Đầu tiên trong templates
- **Nội dung chính:**
  - Navigation bar (thanh điều hướng)
  - Sidebar theo role (customer, admin, shipper, restaurant_owner)
  - Footer
  - CSS và JS chung
- **Tại sao quan trọng:** Tất cả trang khác kế thừa từ đây

#### 7.2. `templates/auth/`

**Mục đích:** Trang đăng nhập và đăng ký

- **Khi nào đọc:** Sau base.html
- **Files:**
  - `login.html`: Form đăng nhập
  - `register.html`: Form đăng ký

#### 7.3. `templates/main/`

**Mục đích:** Trang chủ công khai

- **Khi nào đọc:** Sau auth
- **Files:**
  - `index.html`: Trang chủ hiển thị món ăn theo danh mục

#### 7.4. `templates/customer/`

**Mục đích:** Giao diện cho khách hàng

- **Khi nào đọc:** Sau main
- **Files:**
  - `dashboard.html`: Trang chủ khách hàng
  - `restaurants.html`: Danh sách nhà hàng
  - `restaurant_detail.html`: Chi tiết nhà hàng và menu
  - `cart.html`: Giỏ hàng
  - `checkout.html`: Thanh toán
  - `orders.html`: Lịch sử đơn hàng
  - `order_detail.html`: Chi tiết đơn hàng và đánh giá
  - `reviews.html`: Lịch sử đánh giá

#### 7.5. `templates/restaurant/`

**Mục đích:** Giao diện cho chủ nhà hàng

- **Khi nào đọc:** Sau customer
- **Files:**
  - `register.html`: Đăng ký nhà hàng
  - `pending.html`: Thông báo chờ duyệt
  - `dashboard.html`: Trang quản lý
  - `menus.html`: Danh sách món ăn
  - `menu_form.html`: Form thêm/sửa món ăn
  - `orders.html`: Quản lý đơn hàng
  - `reviews.html`: Đánh giá nhận được

#### 7.6. `templates/shipper/`

**Mục đích:** Giao diện cho tài xế

- **Khi nào đọc:** Sau restaurant
- **Files:**
  - `pending.html`: Thông báo chờ duyệt
  - `dashboard.html`: Trang chủ shipper
  - `orders.html`: Danh sách đơn hàng
  - `order_detail.html`: Chi tiết đơn hàng
  - `stats.html`: Thống kê thu nhập
  - `reviews.html`: Đánh giá nhận được

#### 7.7. `templates/admin/`

**Mục đích:** Giao diện cho admin

- **Khi nào đọc:** Cuối cùng trong templates
- **Files:**
  - `dashboard.html`: Trang tổng quan với thống kê
  - `users.html`: Quản lý người dùng
  - `restaurants.html`: Quản lý nhà hàng
  - `restaurant_owners.html`: Mapping chủ nhà hàng - nhà hàng
  - `shippers.html`: Quản lý tài xế
  - `orders.html`: Quản lý đơn hàng
  - `order_detail.html`: Chi tiết đơn hàng

---

### BƯỚC 8: Đọc Static Files (Tài nguyên)**

#### 8.1. `static/css/style.css`

**Mục đích:** File CSS chứa style cho toàn bộ ứng dụng

- **Khi nào đọc:** Khi cần chỉnh sửa giao diện

#### 8.2. `static/js/main.js`

**Mục đích:** File JavaScript chứa logic phía client

- **Khi nào đọc:** Khi cần hiểu logic frontend

#### 8.3. `static/img/`

**Mục đích:** Thư mục chứa hình ảnh (logo, hình món ăn)

- **Khi nào đọc:** Khi cần thêm/sửa hình ảnh

---

### BƯỚC 9: Đọc Documentation (Tài liệu)**

#### 9.1. `doc/db_nosql.txt`

**Mục đích:** Script khởi tạo database MongoDB với dữ liệu mẫu

- **Khi nào đọc:** Khi cần khởi tạo database hoặc hiểu cấu trúc dữ liệu

#### 9.2. `doc/CHUONG5_NOI_DUNG.md`

**Mục đích:** Tài liệu về cách kết nối MongoDB

- **Khi nào đọc:** Khi cần hiểu cách kết nối database

#### 9.3. `ketnoimongodb.md`

**Mục đích:** Hướng dẫn file nào kết nối MongoDB

- **Khi nào đọc:** Khi cần tìm file kết nối database

---

## 3. Chi tiết từng folder và file

### Folder: `app/`**

**Mục đích:** Thư mục chính chứa toàn bộ code backend của ứng dụng

#### `app/__init__.py`

- **Mục đích:** Khởi tạo Flask application
- **Chức năng:** Tạo app, cấu hình, kết nối database, đăng ký routes
- **Khi nào dùng:** Được gọi khi chạy `run.py`

#### `app/config.py`

- **Mục đích:** Chứa tất cả cấu hình
- **Chức năng:** Cấu hình MongoDB, Flask, upload file, VnPay
- **Khi nào dùng:** Được import bởi `__init__.py` và các file khác

#### `app/database.py`

- **Mục đích:** Quản lý kết nối MongoDB
- **Chức năng:** Khởi tạo kết nối, tạo index, cung cấp database instance
- **Khi nào dùng:** Được gọi khi khởi động app, được import bởi models.py

#### `app/models.py`

- **Mục đích:** Định nghĩa các class model để thao tác database
- **Chức năng:** CRUD operations cho User, Restaurant, Menu, Order, Payment, Review
- **Khi nào dùng:** Được import bởi các file routes để thao tác dữ liệu

---

### Folder: `app/routes/`**

**Mục đích:** Chứa các file xử lý routes (URL endpoints)

#### `app/routes/main.py`

- **Mục đích:** Xử lý trang chủ và routes công khai
- **Routes:** `/` (trang chủ)

#### `app/routes/auth.py`

- **Mục đích:** Xử lý xác thực (đăng nhập, đăng ký, đăng xuất)
- **Routes:** `/login`, `/register`, `/logout`

#### `app/routes/customer.py`

- **Mục đích:** Xử lý tất cả chức năng khách hàng
- **Routes:** `/dashboard`, `/restaurants`, `/cart`, `/checkout`, `/orders`, `/reviews`, `/payment`

#### `app/routes/restaurant.py`

- **Mục đích:** Xử lý chức năng chủ nhà hàng
- **Routes:** `/register`, `/dashboard`, `/menus`, `/orders`, `/reviews`

#### `app/routes/shipper.py`

- **Mục đích:** Xử lý chức năng tài xế
- **Routes:** `/dashboard`, `/orders`, `/stats`, `/reviews`

#### `app/routes/admin.py`

- **Mục đích:** Xử lý chức năng admin
- **Routes:** `/dashboard`, `/users`, `/restaurants`, `/shippers`, `/orders`, `/restaurant-owners`

---

### Folder: `app/utils/`**

**Mục đích:** Chứa các hàm tiện ích và helper

#### `app/utils/auth.py`

- **Mục đích:** Các decorator và hàm hỗ trợ xác thực
- **Chức năng:** `login_required`, `role_required`, `get_current_user`

#### `app/utils/vnpay.py`

- **Mục đích:** Xử lý tích hợp VnPay
- **Chức năng:** Tạo URL thanh toán, xác thực kết quả

#### `app/utils/helpers.py`

- **Mục đích:** Các hàm tiện ích dùng chung
- **Chức năng:** Các hàm helper khác

---

### Folder: `templates/`**

**Mục đích:** Chứa các file HTML template (giao diện)

#### 📄 `templates/base.html`

- **Mục đích:** Template cơ sở, layout chung
- **Chức năng:** Header, sidebar, footer, CSS/JS chung

#### `templates/auth/`

- **Mục đích:** Templates cho đăng nhập/đăng ký
- **Files:** `login.html`, `register.html`

#### `templates/main/`

- **Mục đích:** Templates trang chủ
- **Files:** `index.html`

#### `templates/customer/`

- **Mục đích:** Templates cho khách hàng
- **Files:** `dashboard.html`, `restaurants.html`, `cart.html`, `orders.html`, v.v.

#### `templates/restaurant/`

- **Mục đích:** Templates cho chủ nhà hàng
- **Files:** `dashboard.html`, `menus.html`, `orders.html`, v.v.

#### `templates/shipper/`

- **Mục đích:** Templates cho tài xế
- **Files:** `dashboard.html`, `orders.html`, `stats.html`, v.v.

#### `templates/admin/`

- **Mục đích:** Templates cho admin
- **Files:** `dashboard.html`, `users.html`, `restaurants.html`, v.v.

---

### Folder: `static/`**

**Mục đích:** Chứa các file tĩnh (CSS, JS, hình ảnh)

#### 📁 `static/css/`

- **Mục đích:** File CSS
- **Files:** `style.css`

#### 📁 `static/js/`

- **Mục đích:** File JavaScript
- **Files:** `main.js`

#### 📁 `static/img/`

- **Mục đích:** Hình ảnh (logo, hình món ăn)
- **Files:** `logo.webp`, `bg3.webp`, `pizza.webp`, v.v.

---

### Folder: `doc/`**

**Mục đích:** Chứa tài liệu và script khởi tạo

#### 📄 `doc/db_nosql.txt`

- **Mục đích:** Script MongoDB để khởi tạo database với dữ liệu mẫu
- **Khi nào dùng:** Khi cần khởi tạo database mới

#### 📄 `doc/CHUONG5_NOI_DUNG.md`

- **Mục đích:** Tài liệu về cách kết nối MongoDB
- **Khi nào dùng:** Khi cần hiểu cách kết nối database

---

### File gốc: `run.py`**

**Mục đích:** File khởi chạy ứng dụng (entry point)

- **Chức năng:** Import và tạo Flask app, chạy server trên port 5000
- **Khi nào dùng:** Chạy lệnh `python run.py` để khởi động ứng dụng

### File: `requirements.txt`**

**Mục đích:** Danh sách thư viện Python cần thiết

- **Chức năng:** Liệt kê các package và version
- **Khi nào dùng:** Chạy `pip install -r requirements.txt` để cài đặt dependencies

### File: `README.md`**

**Mục đích:** Hướng dẫn tổng quan về project

- **Chức năng:** Hướng dẫn cài đặt, cấu trúc project, tài khoản mặc định
- **Khi nào dùng:** Đọc đầu tiên để hiểu project

---

## Sơ đồ luồng hoạt động

```
1. run.py
   └─> Tạo Flask app (app/__init__.py)
       ├─> Load cấu hình (app/config.py)
       ├─> Kết nối MongoDB (app/database.py)
       ├─> Đăng ký routes (app/routes/*.py)
       └─> Chạy server

2. User truy cập URL
   └─> Route xử lý (app/routes/*.py)
       ├─> Kiểm tra quyền (app/utils/auth.py)
       ├─> Thao tác dữ liệu (app/models.py)
       │   └─> Kết nối database (app/database.py)
       └─> Render template (templates/*.html)
           └─> Load static files (static/css, js, img)
```

---

## Tóm tắt thứ tự đọc hiểu

1. **Bước 1:** `requirements.txt` → `README.md` (Hiểu tổng quan)
2. **Bước 2:** `app/config.py` → `app/database.py` (Hiểu cấu hình và kết nối)
3. **Bước 3:** `app/__init__.py` → `run.py` (Hiểu cách khởi động)
4. **Bước 4:** `app/models.py` (Hiểu cách thao tác dữ liệu)
5. **Bước 5:** `app/utils/auth.py` → `app/utils/vnpay.py` (Hiểu tiện ích)
6. **Bước 6:** `app/routes/main.py` → `auth.py` → `customer.py` → `restaurant.py` → `shipper.py` → `admin.py` (Hiểu logic xử lý)
7. **Bước 7:** `templates/base.html` → các template khác (Hiểu giao diện)
8. **Bước 8:** `static/` (Hiểu tài nguyên)
9. **Bước 9:** `doc/` (Hiểu tài liệu)

---

## Lưu ý quan trọng

1. **File quan trọng nhất:** `app/database.py` - Kết nối MongoDB
2. **File khởi động:** `run.py` - Entry point của ứng dụng
3. **File cấu hình:** `app/config.py` - Tất cả cấu hình
4. **File models:** `app/models.py` - Thao tác dữ liệu
5. **File routes:** `app/routes/*.py` - Logic xử lý request
6. **File templates:** `templates/*.html` - Giao diện người dùng

---

## Checklist đọc hiểu

- [ ] Đã đọc `requirements.txt` và `README.md`
- [ ] Đã hiểu `app/config.py` và `app/database.py`
- [ ] Đã hiểu `app/__init__.py` và `run.py`
- [ ] Đã hiểu `app/models.py` (tất cả các class)
- [ ] Đã hiểu `app/utils/auth.py`
- [ ] Đã đọc tất cả `app/routes/*.py`
- [ ] Đã xem `templates/base.html`
- [ ] Đã xem các template chính của từng role
- [ ] Đã hiểu cấu trúc `static/`
- [ ] Đã đọc `doc/db_nosql.txt` để hiểu cấu trúc database

---

**Chuc ban doc hieu project thanh cong!**
