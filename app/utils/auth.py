from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import User

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vui lòng đăng nhập để tiếp tục', 'warning')
                return redirect(url_for('auth.login'))
            
            user = User.find_by_id(session['user_id'])
            if not user or user.get('role') not in roles:
                flash('Bạn không có quyền truy cập trang này', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged in user"""
    if 'user_id' in session:
        return User.find_by_id(session['user_id'])
    return None

