import hashlib
import hmac
import urllib.parse
from datetime import datetime
from flask import current_app

class VnPay:
    def __init__(self):
        # Lấy config từ Flask app context
        self.tmn_code = current_app.config.get('VNPAY_TMN_CODE', '')
        self.hash_secret = current_app.config.get('VNPAY_HASH_SECRET', '')
        self.url = current_app.config.get('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
        self.return_url = current_app.config.get('VNPAY_RETURN_URL', 'http://localhost:5000/customer/payment/vnpay_return')
    
    def create_payment_url(self, order_id, amount, order_info, order_type="other", bank_code=""):
        """
        Tạo URL thanh toán VnPay
        
        Args:
            order_id: Mã đơn hàng
            amount: Số tiền (VND)
            order_info: Thông tin đơn hàng
            order_type: Loại đơn hàng
            bank_code: Mã ngân hàng (nếu có)
        
        Returns:
            URL thanh toán VnPay
        """
        # Kiểm tra config
        if not self.tmn_code or self.tmn_code == 'YOUR_TMN_CODE':
            raise ValueError("VNPAY_TMN_CODE chưa được cấu hình. Vui lòng cấu hình trong .env hoặc config.py")
        
        if not self.hash_secret or self.hash_secret == 'YOUR_HASH_SECRET':
            raise ValueError("VNPAY_HASH_SECRET chưa được cấu hình. Vui lòng cấu hình trong .env hoặc config.py")
        
        # Tạo TxnRef từ order_id
        # VnPay yêu cầu TxnRef là số hoặc alphanumeric, tối đa 36 ký tự
        # Tạo TxnRef unique bằng cách kết hợp timestamp và order_id
        import time
        timestamp = int(time.time() * 1000) % 100000000  # Lấy 8 số cuối của timestamp
        order_id_clean = str(order_id).replace('-', '').replace('ObjectId', '')[:20]  # Làm sạch ObjectId
        txn_ref = f"{timestamp}{order_id_clean}"[:36]  # Tối đa 36 ký tự
        
        # Lấy IP thật của user (nếu có)
        from flask import request
        try:
            user_ip = request.remote_addr or '127.0.0.1'
        except:
            user_ip = '127.0.0.1'
        
        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.tmn_code,
            'vnp_Amount': str(int(amount * 100)),  # VnPay yêu cầu số tiền nhân 100, chuyển thành string
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': txn_ref,
            'vnp_OrderInfo': order_info[:255],  # Giới hạn 255 ký tự
            'vnp_OrderType': order_type,
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.return_url,
            'vnp_IpAddr': user_ip,
            'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
        }
        
        if bank_code:
            vnp_params['vnp_BankCode'] = bank_code
        
        # Loại bỏ các giá trị rỗng
        vnp_params = {k: v for k, v in vnp_params.items() if v}
        
        # Sắp xếp params theo thứ tự alphabet
        vnp_params = dict(sorted(vnp_params.items()))
        
        # Tạo query string (không encode vnp_SecureHash)
        query_string = urllib.parse.urlencode(vnp_params)
        
        # Tạo secure hash
        hmac_sha512 = hmac.new(
            bytes(self.hash_secret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # Thêm secure hash vào params
        vnp_params['vnp_SecureHash'] = hmac_sha512
        
        # Tạo URL thanh toán
        payment_url = self.url + '?' + urllib.parse.urlencode(vnp_params)
        
        return payment_url
    
    def verify_payment(self, request_data):
        """
        Xác thực kết quả thanh toán từ VnPay
        Theo tài liệu: https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
        
        Args:
            request_data: Dict chứa các tham số từ VnPay callback
        
        Returns:
            Dict chứa thông tin kết quả thanh toán
        """
        vnp_params = {}
        secure_hash = ''
        
        # Lấy tất cả params bắt đầu bằng vnp_
        for key, value in request_data.items():
            if key.startswith('vnp_'):
                if key == 'vnp_SecureHash':
                    secure_hash = value
                elif key == 'vnp_SecureHashType':
                    # Bỏ qua vnp_SecureHashType khi tạo hash
                    continue
                else:
                    vnp_params[key] = value
        
        # Sắp xếp params theo thứ tự alphabet (theo tài liệu)
        vnp_params = dict(sorted(vnp_params.items()))
        
        # Tạo query string (không encode, theo tài liệu)
        query_string = urllib.parse.urlencode(vnp_params)
        
        # Tạo secure hash để so sánh (HMAC SHA512)
        hmac_sha512 = hmac.new(
            bytes(self.hash_secret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # Kiểm tra secure hash
        if secure_hash != hmac_sha512:
            return {
                'success': False,
                'message': 'Invalid secure hash - Chu ky khong hop le'
            }
        
        # Kiểm tra response code
        response_code = vnp_params.get('vnp_ResponseCode', '')
        
        if response_code == '00':
            return {
                'success': True,
                'order_id': vnp_params.get('vnp_TxnRef'),
                'transaction_id': vnp_params.get('vnp_TransactionNo'),
                'amount': int(vnp_params.get('vnp_Amount', 0)) / 100,
                'bank_code': vnp_params.get('vnp_BankCode'),
                'pay_date': vnp_params.get('vnp_PayDate'),
                'transaction_status': vnp_params.get('vnp_TransactionStatus', ''),
                'message': 'Thanh toán thành công'
            }
        else:
            return {
                'success': False,
                'order_id': vnp_params.get('vnp_TxnRef'),
                'response_code': response_code,
                'transaction_id': vnp_params.get('vnp_TransactionNo'),
                'message': self.get_response_message(response_code)
            }
    
    @staticmethod
    def get_response_message(response_code):
        """
        Lấy thông báo lỗi từ response code
        Theo tài liệu: https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
        """
        messages = {
            '00': 'Giao dịch thành công',
            '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường)',
            '09': 'Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng chưa đăng ký dịch vụ InternetBanking tại ngân hàng',
            '10': 'Giao dịch không thành công do: Khách hàng xác thực thông tin thẻ/tài khoản không đúng quá 3 lần',
            '11': 'Giao dịch không thành công do: Đã hết hạn chờ thanh toán. Xin quý khách vui lòng thực hiện lại giao dịch',
            '12': 'Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng bị khóa',
            '13': 'Giao dịch không thành công do: Quý khách nhập sai mật khẩu xác thực giao dịch (OTP). Xin quý khách vui lòng thực hiện lại giao dịch',
            '24': 'Giao dịch không thành công do: Khách hàng hủy giao dịch',
            '51': 'Giao dịch không thành công do: Tài khoản của quý khách không đủ số dư để thực hiện giao dịch',
            '65': 'Giao dịch không thành công do: Tài khoản của Quý khách đã vượt quá hạn mức giao dịch trong ngày',
            '75': 'Ngân hàng thanh toán đang bảo trì',
            '79': 'Giao dịch không thành công do: KH nhập sai mật khẩu thanh toán quá số lần quy định. Xin quý khách vui lòng thực hiện lại giao dịch',
            '99': 'Các lỗi khác (lỗi còn lại, không có trong danh sách mã lỗi đã liệt kê)'
        }
        return messages.get(response_code, f'Lỗi không xác định (Code: {response_code})')

