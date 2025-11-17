from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from app.utils.auth import login_required
from app.utils.helpers import to_object_id
from app import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if not phone or not password:
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('auth/login.html')
        
        user = User.find_by_phone(phone)
        
        if user:
            user_password = user.get('password', '')
            
            # Kiểm tra xem password có phải là bcrypt hash không (bắt đầu bằng $2a$ hoặc $2b$)
            is_bcrypt_hash = user_password.startswith('$2a$') or user_password.startswith('$2b$')
            
            password_valid = False
            
            if is_bcrypt_hash:
                # Password đã được hash, kiểm tra bằng bcrypt
                try:
                    password_valid = bcrypt.check_password_hash(user_password, password)
                except ValueError:
                    # Hash không hợp lệ, có thể cần hash lại
                    password_valid = False
            else:
                # Password là plain text (từ dữ liệu mẫu), so sánh trực tiếp
                # Sau đó hash lại và lưu vào database
                password_valid = (user_password == password)
                
                if password_valid:
                    # Hash lại password và lưu vào database
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    User.update(str(user['_id']), {'password': hashed_password})
            
            if password_valid:
                session['user_id'] = str(user['_id'])
                session['user_role'] = user.get('role')
                session['user_name'] = user.get('name')
                session.permanent = True
                
                # Load cart từ database vào session (nếu là customer)
                if user.get('role') == 'customer':
                    cart = User.get_cart(str(user['_id']))
                    if cart:
                        session['cart'] = cart
                        session.modified = True
                
            # Redirect based on role
            role = user.get('role')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'shipper':
                return redirect(url_for('shipper.dashboard'))
            elif role == 'restaurant_owner':
                return redirect(url_for('restaurant.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
        
        flash('Số điện thoại hoặc mật khẩu không đúng', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - Only customer and restaurant_owner"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'customer')
        
        # Validation
        if not all([phone, name, password]):
            flash('Vui lòng nhập đầy đủ thông tin', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'danger')
            return render_template('auth/register.html')
        
        # Chỉ cho phép đăng ký customer hoặc restaurant_owner
        if role not in ['customer', 'restaurant_owner']:
            flash('Vai trò không hợp lệ. Chỉ có thể đăng ký với vai trò Khách hàng hoặc Chủ nhà hàng.', 'danger')
            return render_template('auth/register.html')
        
        # Check if phone exists
        if User.find_by_phone(phone):
            flash('Số điện thoại đã được sử dụng', 'danger')
            return render_template('auth/register.html')
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user_data = {
            'phone': phone,
            'name': name,
            'password': hashed_password,
            'role': role,
            'status': 'active' if role == 'customer' else 'pending'  # Customer active ngay, restaurant_owner cần admin duyệt
        }
        
        User.create(user_data)
        
        if role == 'restaurant_owner':
            flash('Đăng ký thành công! Tài khoản của bạn đang chờ admin duyệt. Vui lòng đợi thông báo.', 'success')
        else:
            flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Lưu cart vào database trước khi đăng xuất (nếu là customer)
    user_id = session.get('user_id')
    if user_id and session.get('user_role') == 'customer':
        cart = session.get('cart', {})
        if cart:
            User.save_cart(user_id, cart)
    
    session.clear()
    flash('Đã đăng xuất thành công', 'info')
    return redirect(url_for('main.index'))

