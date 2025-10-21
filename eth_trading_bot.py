
import time
import hmac
import hashlib
import requests
from datetime import datetime

print("=== 🚀 ETH TRADING BOT - DIRECT API KEYS ===")

# 🔑 API KEY'LERİ DOĞRUDAN KODA YAZ
API_KEY = "YOhSlQdyaqnDWf1Gvc2DqrjHmTQWWta1zLFlkW22Ro0Z8ZYZ131nPVbbBXH7BGyk"
API_SECRET = "EjcrH6FYCApdXtnaPykubUEAmNKrYpIaJrxd7KPLkt57c1CKvEYMVxzGNwpsfAou"
BASE_URL = "https://testnet.binancefuture.com"

SYMBOL = "ETHUSDT"
LEVERAGE = 20

print(f"🔑 API_KEY: {API_KEY[:16]}...")
print(f"🔐 API_SECRET: {API_SECRET[:16]}...")
print(f"⏰ Zaman: {datetime.now()}")

def binance_request(endpoint, params=None, method='GET'):
    """Binance API request"""
    try:
        timestamp = int(time.time() * 1000)
        
        if params is None:
            params = {}
        
        params['timestamp'] = timestamp
        params['recvWindow'] = 10000
        
        # Query string
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        # Signature
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': API_KEY}
        url = f"{BASE_URL}{endpoint}"
        
        print(f"🔗 {method} {endpoint}")
        print(f"📝 Query: {query_string}")
        print(f"🔄 Signature: {signature[:16]}...")
        
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=10)
        else:
            response = requests.post(url, data=params, headers=headers, timeout=10)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Başarılı!")
            return result
        else:
            print(f"❌ Hata: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Request hatası: {e}")
        return None

def main():
    print("\n" + "="*50)
    print("🤖 ETH/USDT TRADING BOT - DIRECT KEYS")
    print("="*50)
    
    # 1. SERVER TIME TEST
    print("\n1️⃣ Server Time Test...")
    time_url = f"{BASE_URL}/fapi/v1/time"
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
    
    # 3. KÜÇÜK BUY ORDER
    print("\n3️⃣ KÜÇÜK BUY ORDER TEST...")
    small_buy = binance_request('/fapi/v1/order', {
        'symbol': SYMBOL,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': 5
    }, 'POST')
    
    if small_buy:
        print("🎉 🎉 🎉 BAŞARILI! ORDER ÇALIŞTI! 🎉 🎉 🎉")
        print(f"Order: {small_buy}")
    else:
        print("💥 Order başarısız")
    
    print("\n" + "="*50)
    print("✅ Test tamamlandı!")
    print("="*50)

if __name__ == "__main__":
    main()
