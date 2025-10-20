import os
import time
import hmac
import hashlib
import requests
from datetime import datetime
import json

print("=== 🚀 ETH TRADING BOT - FIXED VERSION ===")
print(f"⏰ Zaman: {datetime.now()}")

# API Bilgileri - DEBUG MOD
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = "https://testnet.binance.com"

print(f"🔑 API_KEY: {API_KEY[:10]}..." if API_KEY else "❌ API_KEY YOK")
print(f"🔐 API_SECRET: {API_SECRET[:10]}..." if API_SECRET else "❌ API_SECRET YOK")

if not API_KEY or not API_SECRET:
    print("💥 CRITICAL: API KEY veya SECRET bulunamadı!")
    exit()

SYMBOL = "ETHUSDT"

def binance_request(endpoint, params=None, method='GET'):
    """DÜZGÜN signature ile request"""
    try:
        # Timestamp
        timestamp = int(time.time() * 1000)
        
        if params is None:
            params = {}
        
        params['timestamp'] = timestamp
        params['recvWindow'] = 5000
        
        # Query string oluştur - SIRALI
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        # Signature - KESİN DOĞRU
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        
        # Headers
        headers = {
            'X-MBX-APIKEY': API_KEY,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # URL
        url = f"{BASE_URL}{endpoint}"
        
        print(f"🔗 {method} {endpoint}")
        print(f"📝 Query: {query_string}")
        print(f"🔄 Signature: {signature[:16]}...")
        
        # Request
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=10)
        else:
            response = requests.post(url, data=params, headers=headers, timeout=10)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Başarılı: {result}")
            return result
        else:
            print(f"❌ Hata: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Request hatası: {e}")
        return None

def main():
    print("\n" + "="*50)
    print("🎯 BOT TEST BAŞLIYOR - ADIM ADIM")
    print("="*50)
    
    # 1. SERVER TIME TEST (signature gerekmez)
    print("\n1️⃣ Server Time Test...")
    time_url = "https://testnet.binancefuture.com/fapi/v1/time"
    time_response = requests.get(time_url)
    if time_response.status_code == 200:
        print("✅ Binance bağlantısı çalışıyor")
    else:
        print("❌ Binance bağlantı hatası")
        return
    
    # 2. BAKİYE KONTROLÜ
    print("\n2️⃣ Bakiye Kontrolü...")
    balance = binance_request('/fapi/v2/balance')
    if balance:
        for asset in balance:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['balance'])
                print(f"💰 Bakiye: {usdt_balance} USDT")
                break
    
    # 3. SADECE BUY ORDER DENEYELİM
    print("\n3️⃣ KÜÇÜK BUY ORDER TEST...")
    small_buy = binance_request('/fapi/v1/order', {
        'symbol': SYMBOL,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': 1  # ÇOK KÜÇÜK miktar
    }, 'POST')
    
    if small_buy:
        print("🎉 🎉 🎉 BAŞARILI! ORDER ÇALIŞTI! 🎉 🎉 🎉")
        print(f"Order Detay: {small_buy}")
    else:
        print("💥 Order başarısız - API Secret hatalı!")
    
    print("\n" + "="*50)
    print("✅ Test tamamlandı!")
    print("="*50)

if __name__ == "__main__":
    main()
