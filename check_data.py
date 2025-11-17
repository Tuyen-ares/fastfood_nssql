"""
Script kiểm tra dữ liệu trong database fastfood
"""
from pymongo import MongoClient

# Kết nối MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fastfood']

print("=" * 50)
print("KIỂM TRA DỮ LIỆU TRONG DATABASE")
print("=" * 50)

# Kiểm tra từng collection
collections = ['users', 'restaurants', 'menus', 'orders', 'payments']

for collection_name in collections:
    collection = db[collection_name]
    count = collection.count_documents({})
    print(f"\n📦 {collection_name.upper()}: {count} documents")
    
    if count > 0:
        # Hiển thị một vài document mẫu
        sample = list(collection.find().limit(3))
        for i, doc in enumerate(sample, 1):
            if collection_name == 'users':
                print(f"  {i}. {doc.get('name', 'N/A')} - {doc.get('phone', 'N/A')} ({doc.get('role', 'N/A')})")
            elif collection_name == 'restaurants':
                print(f"  {i}. {doc.get('name', 'N/A')} - {doc.get('addr', 'N/A')}")
            elif collection_name == 'menus':
                menu_name = doc.get('name', 'N/A')
                rest_id = doc.get('rest_id', 'N/A')
                # Tìm tên nhà hàng
                restaurant = db.restaurants.find_one({'_id': rest_id})
                rest_name = restaurant.get('name', 'Unknown') if restaurant else 'Unknown'
                print(f"  {i}. {menu_name} - {rest_name} - {doc.get('price', 0):,} đ")
            elif collection_name == 'orders':
                print(f"  {i}. Order ID: {str(doc.get('_id', 'N/A'))[:8]} - Status: {doc.get('status', 'N/A')}")
            elif collection_name == 'payments':
                print(f"  {i}. Payment ID: {str(doc.get('_id', 'N/A'))[:8]} - Status: {doc.get('status', 'N/A')}")
    else:
        print(f"  ⚠️ Collection {collection_name} trống!")

print("\n" + "=" * 50)
print("KIỂM TRA MENU THEO NHÀ HÀNG")
print("=" * 50)

# Kiểm tra menu của từng nhà hàng
restaurants = list(db.restaurants.find())
for rest in restaurants:
    rest_id = rest['_id']
    menus = list(db.menus.find({'rest_id': rest_id}))
    print(f"\n🍽️ {rest.get('name', 'N/A')}: {len(menus)} món")
    for menu in menus:
        print(f"   - {menu.get('name', 'N/A')}: {menu.get('price', 0):,} đ")

print("\n" + "=" * 50)
print("KẾT LUẬN")
print("=" * 50)

total_menus = db.menus.count_documents({})
if total_menus == 0:
    print("❌ KHÔNG CÓ MÓN NÀO TRONG DATABASE!")
    print("👉 Bạn cần chạy script db_nosql.txt trong MongoDB Compass")
else:
    print(f"✅ Có {total_menus} món trong database")

