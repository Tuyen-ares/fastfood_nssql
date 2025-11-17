"""
Script để kiểm tra và hiển thị mapping giữa chủ nhà hàng và nhà hàng
"""
from app import create_app
from app.database import get_db
from app.models import User, Restaurant

app = create_app()

with app.app_context():
    db = get_db()
    
    print("=" * 60)
    print("KIỂM TRA MAPPING CHỦ NHÀ HÀNG - NHÀ HÀNG")
    print("=" * 60)
    
    # Lấy tất cả chủ nhà hàng
    owners = User.find_by_role('restaurant_owner')
    
    if not owners:
        print("\n❌ Không có chủ nhà hàng nào trong hệ thống")
    else:
        print(f"\n📊 Tổng số chủ nhà hàng: {len(owners)}")
        print("-" * 60)
        
        for owner in owners:
            owner_id = str(owner['_id'])
            owner_name = owner.get('name', 'N/A')
            owner_phone = owner.get('phone', 'N/A')
            
            print(f"\n👤 Chủ nhà hàng: {owner_name}")
            print(f"   📱 Số điện thoại: {owner_phone}")
            print(f"   🆔 ID: {owner_id}")
            
            # Tìm nhà hàng của chủ này
            restaurants = Restaurant.find_by_owner(owner_id)
            
            if restaurants:
                print(f"   🏪 Số nhà hàng quản lý: {len(restaurants)}")
                for idx, rest in enumerate(restaurants, 1):
                    print(f"      {idx}. {rest.get('name', 'N/A')} (ID: {rest['_id']})")
                    print(f"         - Địa chỉ: {rest.get('addr', 'N/A')}")
                    print(f"         - Trạng thái: {rest.get('status', 'N/A')}")
            else:
                print(f"   ⚠️  Chưa có nhà hàng nào")
    
    print("\n" + "=" * 60)
    print("KIỂM TRA NHÀ HÀNG KHÔNG CÓ CHỦ")
    print("=" * 60)
    
    # Tìm nhà hàng không có owner_id
    restaurants_no_owner = list(db.restaurants.find({
        '$or': [
            {'owner_id': {'$exists': False}},
            {'owner_id': None}
        ]
    }))
    
    if restaurants_no_owner:
        print(f"\n⚠️  Tìm thấy {len(restaurants_no_owner)} nhà hàng không có chủ:")
        for rest in restaurants_no_owner:
            print(f"   - {rest.get('name', 'N/A')} (ID: {rest['_id']})")
    else:
        print("\n✅ Tất cả nhà hàng đều có chủ")
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ")
    print("=" * 60)
    
    total_restaurants = db.restaurants.count_documents({})
    restaurants_with_owner = db.restaurants.count_documents({'owner_id': {'$exists': True, '$ne': None}})
    
    print(f"Tổng số nhà hàng: {total_restaurants}")
    print(f"Nhà hàng có chủ: {restaurants_with_owner}")
    print(f"Nhà hàng chưa có chủ: {total_restaurants - restaurants_with_owner}")

