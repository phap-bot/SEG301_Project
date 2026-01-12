from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
import sys
import datetime

# ==============================================================================
# CẤU HÌNH (LẤY TỪ FILE TRƯỚC)
# ==============================================================================
CONFIG = {
    'app_id': '2019447845565970',
    'app_secret': '27ead38207c2d371f4938eddbe4b6b33',
    'access_token': 'EAAcsrVd6NhIBQUNyZCeeXmNHLbbRZCOxKIMfYspHrf9knoXxGuTgMiDnEHXKjIIzWIpmniCt655rlR8smNUGzKxPXByHRvxlgZA28mDXixNwQSH2NPIhzRQJ9tFCeENPGAffwPnWvcWwwHV8vJoKoQkKvZClfhP95yiPwcZBZBSVdZA1OXzKJovPNephIh7q2rxWZCt8UVyUS7kxZA2ZC8VTUN7GQ6CoAZAZAre5bIbRp9GFZAiy6ZBoERtOQPXLtUOdq0FK2EAcYgWX7ZCo3hg9ZApG1R0ZBh9oq',
    # ID Tài khoản quảng cáo (Lấy từ kết quả check BM trước đó: 899823892711424)
    # Lưu ý: API yêu cầu thêm tiền tố 'act_'
    'ad_account_id': 'act_899823892711424' 
}

def init_api():
    try:
        FacebookAdsApi.init(CONFIG['app_id'], CONFIG['app_secret'], CONFIG['access_token'])
        print("✅ Kết nối API thành công!")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        sys.exit(1)

def create_retention_campaign():
    print(f"\n--- TẠO CAMPAIGN MỒI (TRUST BUILDING) ---")
    account = AdAccount(CONFIG['ad_account_id'])
    
    # BƯỚC 1: TẠO CAMPAIGN (CHIẾN DỊCH)
    print("1️⃣  Đang tạo Campaign...", end=" ")
    try:
        params = {
            'name': 'Campaign Mồi - Tăng Trust (Auto)',
            'objective': 'OUTCOME_TRAFFIC', # Mục tiêu Traffic (Lưu lượng truy cập) dễ duyệt
            'status': 'PAUSED', # Tạo xong để Pause, bạn review rồi bật sau
            'special_ad_categories': [],
        }
        campaign = account.create_campaign(params=params)
        print(f"✅ OK! ID: {campaign['id']}")
    except Exception as e:
        print(f"❌ Lỗi tạo Campaign: {e}")
        return

    # BƯỚC 2: TẠO AD SET (NHÓM QUẢNG CÁO)
    print("2️⃣  Đang tạo Ad Set...", end=" ")
    try:
        # Thời gian bắt đầu: Ngay bây giờ
        start_time = datetime.datetime.now()
        # Thời gian kết thúc: Sau 7 ngày (Để chạy mồi)
        end_time = start_time + datetime.timedelta(days=7)
        
        params = {
            'name': 'AdSet Mồi - VN - 18+',
            'campaign_id': campaign['id'],
            'daily_budget': 50000, # 50.000 VND/ngày (Ngân sách nhỏ an toàn)
            'billing_event': 'IMPRESSIONS',
            'optimization_goal': 'LINK_CLICKS',
            'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'targeting': {
                'geo_locations': {
                    'countries': ['VN'], # Chạy tại Việt Nam
                },
                'age_min': 20,
                'age_max': 45,
            },
            'status': 'PAUSED',
        }
        adset = account.create_ad_set(params=params)
        print(f"✅ OK! ID: {adset['id']}")
    except Exception as e:
        print(f"❌ Lỗi tạo Ad Set: {e}")
        return

    print("\n---------------------------------------------------")
    print("🎉 ĐÃ TẠO XONG KHUNG CHIẾN DỊCH!")
    print("👉 Bước tiếp theo: Bạn hãy vào Trình Quản Lý Quảng Cáo.")
    print(f"👉 Link: https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={CONFIG['ad_account_id'].replace('act_', '')}")
    print("👉 Tìm chiến dịch 'Campaign Mồi', vào phần Quảng cáo (Ads) để thêm hình ảnh/bài viết rồi BẬT (Publish).")

if __name__ == '__main__':
    init_api()
    create_retention_campaign()
