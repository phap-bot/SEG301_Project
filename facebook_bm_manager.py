import sys
import json
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.adaccount import AdAccount

# ==============================================================================
# HƯỚNG DẪN CẤU HÌNH (CONFIGURATION)
# ==============================================================================
# 1. Truy cập: https://developers.facebook.com/apps/
# 2. Tạo một App "Business" (Doanh nghiệp).
# 3. Vào phần "Cài đặt" -> "Thông tin cơ bản" để lấy App ID và App Secret.
# 4. Vào "Graph API Explorer" hoặc set up "System User" trong cài đặt BM để lấy Access Token.
#    (Quyền cần thiết: ads_management, business_management)
# 5. Business ID: Lấy trên URL khi bạn vào trình quản lý doanh nghiệp (business.facebook.com)
# ==============================================================================

CONFIG = {
    'app_id': '2019447845565970',
    'app_secret': '27ead38207c2d371f4938eddbe4b6b33',
    'access_token': 'EAAcsrVd6NhIBQUNyZCeeXmNHLbbRZCOxKIMfYspHrf9knoXxGuTgMiDnEHXKjIIzWIpmniCt655rlR8smNUGzKxPXByHRvxlgZA28mDXixNwQSH2NPIhzRQJ9tFCeENPGAffwPnWvcWwwHV8vJoKoQkKvZClfhP95yiPwcZBZBSVdZA1OXzKJovPNephIh7q2rxWZCt8UVyUS7kxZA2ZC8VTUN7GQ6CoAZAZAre5bIbRp9GFZAiy6ZBoERtOQPXLtUOdq0FK2EAcYgWX7ZCo3hg9ZApG1R0ZBh9oq',
    'business_id': '1183815553693266'
}

def init_api():
    """Khởi tạo kết nối đến Facebook API"""
    try:
        FacebookAdsApi.init(CONFIG['app_id'], CONFIG['app_secret'], CONFIG['access_token'])
        print("✅ Kết nối API thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        print("Vui lòng kiểm tra lại App ID, Secret và Access Token trong phần CONFIG.")
        sys.exit(1)

def get_bm_info(bm_id):
    """Lấy thông tin cơ bản của BM"""
    try:
        bm = Business(bm_id)
        fields = [
            'name',
            'id',
            'verification_status',
            'primary_page'
        ]
        bm_data = bm.api_get(fields=fields)
        print(f"\n--- THÔNG TIN BM: {bm_data.get('name', 'Unknown')} ---")
        print(f"ID: {bm_data.get('id')}")
        print(f"Trạng thái xác minh: {bm_data.get('verification_status', 'Chưa xác định')}")
        print(f"Ngày tạo: {bm_data.get('creation_time')}")
        return bm
    except Exception as e:
        print(f"❌ Không thể lấy thông tin BM (ID: {bm_id}): {e}")
        return None

def check_ad_limits(bm):
    """Kiểm tra số tài khoản và trả về số lượng hiện tại"""
    print("\n--- KIỂM TRA LIMIT & TÀI KHOẢN ---")
    try:
        owned_accounts = bm.get_owned_ad_accounts(fields=['name', 'account_id', 'amount_spent', 'account_status', 'currency'])
        count = len(owned_accounts)
        print(f"🔢 Tổng số tài khoản quảng cáo đang sở hữu: {count}")
        
        for acc in owned_accounts:
            status = "Hoạt động" if acc['account_status'] == 1 else f"Status Code {acc['account_status']}"
            print(f" - [{acc['account_id']}] {acc['name']} ({acc['currency']}) | {status}")
            
        return count
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra tài khoản: {e}")
        return 0

def kick_bm_limit(bm, current_count):
    """Cưỡng ép tạo tài khoản để kích limit với nhiều chiến lược bypass"""
    print(f"\n--- 🚀 KICK BM LIMIT (AUTO CREATE - BYPASS MODE) ---")
    
    target_slots = 5 
    if current_count >= target_slots:
        print("✅ BM của bạn đã đạt BM5 hoặc cao hơn rồi!")
        return

    print(f"Đang thử tạo thêm {target_slots - current_count} tài khoản nữa...")
    
    for i in range(current_count + 1, target_slots + 1):
        name_suffix = f"TK_KICK_{i}"
        account_name = f"{bm['name']} - {name_suffix}"
            
        # CHIẾN LƯỢC 1: Thử tạo chuẩn (VND) nhưng bỏ hết params thừa
        try:
            print(f"🔹 [Strategy 1] Thử tạo '{account_name}' (VND sạch)...", end=" ")
            params = {
                'name': account_name,
                'currency': 'VND',
                'timezone_id': 26, 
                'end_advertiser': bm['id']
            }
            res = bm.create_ad_account(params=params)
            print(f"✅ THÀNH CÔNG! ID: {res['id']}")
            continue
        except Exception as e:
            print("❌ Thất bại.")
            if "maximum number" in str(e): 
                print("⚠️ Đã chạm trần BM limit.")
                break

        # CHIẾN LƯỢC 2: Thử tạo bằng USD (Đôi khi lách được check vùng)
        try:
            print(f"🔹 [Strategy 2] Thử tạo '{account_name}' (USD - Bypass)...", end=" ")
            params_usd = {
                'name': account_name + "_USD",
                'currency': 'USD',
                'timezone_id': 7, # America/Los_Angeles
                'end_advertiser': bm['id']
            }
            res = bm.create_ad_account(params=params_usd)
            print(f"✅ THÀNH CÔNG! ID: {res['id']}")
            continue
        except Exception as e:
            print("❌ Thất bại.")
            # In lỗi chi tiết của lần thử cuối cùng
            print(f"� Chi tiết lỗi: {e}")
            if "agency" in str(e).lower():
                print("⚠️ Vẫn dính lỗi Agency. Có thể BM này bị gắn cờ bắt buộc.")

if __name__ == '__main__':
    # Kiểm tra cấu hình
    if 'DÁN_' in CONFIG['access_token']:
        print("⚠️  Vui lòng điền thông tin vào CONFIG.")
        sys.exit(0)

    init_api()
    my_bm = get_bm_info(CONFIG['business_id'])
    
    if my_bm:
        current_count = check_ad_limits(my_bm)
        
        # Tự động chạy lệnh Kick
        print("\nBắt đầu quy trình kích BM sau 3 giây...")
        import time
        time.sleep(3)
        kick_bm_limit(my_bm, current_count)
