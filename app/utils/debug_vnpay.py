"""
Utility để debug VnPay integration
Chạy script này để kiểm tra cấu hình VnPay
"""
from app import create_app
from app.utils.vnpay import VnPay

app = create_app()

with app.app_context():
    print("=" * 50)
    print("KIỂM TRA CẤU HÌNH VNPAY")
    print("=" * 50)
    
    # Kiểm tra config
    tmn_code = app.config.get('VNPAY_TMN_CODE', '')
    hash_secret = app.config.get('VNPAY_HASH_SECRET', '')
    return_url = app.config.get('VNPAY_RETURN_URL', '')
    
    print(f"\nTMN Code: {tmn_code}")
    print(f"Hash Secret: {'*' * len(hash_secret) if hash_secret else 'CHƯA CẤU HÌNH'}")
    print(f"Return URL: {return_url}")
    
    # Kiểm tra có cấu hình chưa
    if not tmn_code or tmn_code == 'YOUR_TMN_CODE':
        print("\nVNPAY_TMN_CODE chua duoc cau hinh!")
        print("Vui long cau hinh trong .env hoac config.py")
    else:
        print("\nTMN Code da duoc cau hinh")
    
    if not hash_secret or hash_secret == 'YOUR_HASH_SECRET':
        print("VNPAY_HASH_SECRET chua duoc cau hinh!")
        print("Vui long cau hinh trong .env hoac config.py")
    else:
        print("Hash Secret da duoc cau hinh")
    
    # Test tạo payment URL
    if tmn_code and hash_secret and tmn_code != 'YOUR_TMN_CODE' and hash_secret != 'YOUR_HASH_SECRET':
        try:
            vnpay = VnPay()
            test_url = vnpay.create_payment_url(
                order_id="TEST123",
                amount=100000,
                order_info="Test payment"
            )
            print(f"\nTao URL thanh cong!")
            print(f"URL: {test_url[:100]}...")
        except Exception as e:
            print(f"\nLoi khi tao URL: {e}")
    
    print("\n" + "=" * 50)

