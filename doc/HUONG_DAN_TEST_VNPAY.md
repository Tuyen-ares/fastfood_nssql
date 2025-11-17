# Hướng dẫn test thanh toán VnPay

## ⚠️ Lỗi thường gặp: "Có lỗi xảy ra trong quá trình xử lý"

### Nguyên nhân 1: Chưa cấu hình Return URL và IPN URL

**QUAN TRỌNG NHẤT:** Bạn PHẢI cấu hình Return URL và IPN URL trong VnPay Portal trước khi test!

1. **Đăng nhập Merchant Admin:**
   - URL: https://sandbox.vnpayment.vn/merchantv2/
   - Email: hoantuyen2004@gmail.com
   - Mật khẩu: (Mật khẩu bạn đã đặt)

2. **Vào phần cấu hình:**
   - Tìm **Cấu hình** hoặc **Settings**
   - Tìm **Return URL** hoặc **Callback URL**
   - Tìm **IPN URL**

3. **Điền URL (Nếu dùng Ngrok):**
   - Return URL: `https://your-ngrok-url.ngrok.io/customer/payment/vnpay_return`
   - IPN URL: `https://your-ngrok-url.ngrok.io/customer/payment/vnpay_ipn`
   - **Lưu cấu hình**

4. **Cập nhật trong `app/config.py`:**
   ```python
   VNPAY_RETURN_URL = 'https://your-ngrok-url.ngrok.io/customer/payment/vnpay_return'
   VNPAY_IPN_URL = 'https://your-ngrok-url.ngrok.io/customer/payment/vnpay_ipn'
   ```

### Nguyên nhân 2: Dùng sai thẻ test

**Bạn đang dùng:** Thẻ JCB quốc tế (3337000000000008) - Có thể không hoạt động trong sandbox

**Nên dùng thẻ test từ email VnPay:**

#### Thẻ test NCB (Nội địa) - Khuyến nghị:
- **Ngân hàng:** NCB
- **Số thẻ:** `9704198526191432198`
- **Tên chủ thẻ:** `NGUYEN VAN A`
- **Ngày hết hạn:** `07/15` (hoặc bất kỳ ngày nào trong tương lai)
- **Mật khẩu OTP:** `123456`
- **CVC/CVV:** Có thể để trống hoặc nhập bất kỳ

#### Cách thanh toán với thẻ NCB:
1. Chọn phương thức: **Thẻ ATM - Tài khoản ngân hàng nội địa**
2. Nhập số thẻ: `9704198526191432198`
3. Nhập thông tin khác theo yêu cầu
4. Khi yêu cầu OTP, nhập: `123456`

### Nguyên nhân 3: Chưa chạy Ngrok (nếu test local)

Nếu bạn đang test local và chưa dùng Ngrok, VnPay không thể callback về `localhost`.

**Giải pháp:**
1. Chạy Flask app: `python run.py`
2. Chạy Ngrok: `ngrok http 5000`
3. Copy URL từ Ngrok
4. Cấu hình URL trong VnPay Portal và `config.py`

## ✅ Checklist trước khi test

- [ ] Đã cấu hình Return URL trong VnPay Portal
- [ ] Đã cấu hình IPN URL trong VnPay Portal
- [ ] Đã cập nhật URL trong `app/config.py`
- [ ] Đã chạy Flask app
- [ ] Đã chạy Ngrok (nếu test local)
- [ ] Sử dụng đúng thẻ test từ email

## 🔍 Debug

Nếu vẫn lỗi, kiểm tra:

1. **Console log trong browser (F12):** Xem có lỗi JavaScript không
2. **Terminal log:** Xem có lỗi từ Flask app không
3. **VnPay Portal:** Xem giao dịch có được tạo không
4. **Kiểm tra Return URL:** Đảm bảo URL đúng và có thể truy cập được

## 📞 Hỗ trợ

Nếu vẫn không được, liên hệ:
- Email: support.vnpayment@vnpay.vn
- Hotline: 1900 55 55 77

