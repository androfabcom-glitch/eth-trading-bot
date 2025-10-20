import os
import time
import hmac
import hashlib
import requests
from datetime import datetime
import json

print("=== 🚀 ETH TRADING BOT BAŞLATILDI ===")
print(f"⏰ Zaman: {datetime.now()}")

# API Bilgileri
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = "https://testnet.binancefuture.com"

def make_request(endpoint, params=None, method='GET'):
    try:
        print(f"🔗 İstek gönderiliyor: {endpoint}")
        
        # Timestamp ve signature oluştur
        timestamp = int(time.time() * 1000)
        
        if params is None:
            params = {}
        
        params['timestamp'] = timestamp
        
        # Signature oluşturma
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            API_SECRET.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        
        # Header
        headers = {'X-MBX-APIKEY': API_KEY}
        
        # URL
        url = f"{BASE_URL}{endpoint}"
        
        print(f"📡 URL: {url}")
        
        # Request gönder
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.post(url, data=params, headers=headers)
        
        print(f"✅ API Yanıt Kodu: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Başarılı: {result}")
            return result
        else:
            print(f"❌ Hata: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 API Hatası: {e}")
        return None

def main():
    print("\n" + "="*50)
    print("🤖 ETH/USDT TRADING BOT ÇALIŞIYOR")
    print("="*50)
    
    # 1. Bakiyeyi kontrol et
    print("\n1️⃣ Bakiye kontrol ediliyor...")
    balance_data = make_request('/fapi/v2/balance')
    
    usdt_balance = 0
    if balance_data:
        for asset in balance_data:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['balance'])
                print(f"💰 Bakiye: {usdt_balance} USDT")
                break
        if usdt_balance == 0:
            print("❌ USDT bakiyesi bulunamadı!")
            return
    
    # 2. Kaldıraç ayarla
    print("\n2️⃣ Kaldıraç ayarlanıyor...")
    leverage_result = make_request('/fapi/v1/leverage', {
        'symbol': 'ETHUSDT',
        'leverage': 20
    }, 'POST')
    
    if leverage_result:
        print(f"⚡ Kaldıraç 20x ayarlandı")
    
    # 3. Pozisyon kontrolü
    print("\n3️⃣ Mevcut pozisyon kontrol ediliyor...")
    positions = make_request('/fapi/v2/positionRisk', {'symbol': 'ETHUSDT'})
    
    current_position = 0
    if positions:
        for pos in positions:
            amount = float(pos.get('positionAmt', 0))
            if amount != 0:
                current_position = amount
                print(f"📊 Mevcut Pozisyon: {amount} ETH")
                break
    
    if current_position == 0:
        print("📭 Açık pozisyon bulunamadı")
    
    # 4. Mum verilerini al
    print("\n4️⃣ Mum verileri alınıyor...")
    klines = make_request('/fapi/v1/klines', {
        'symbol': 'ETHUSDT',
        'interval': '1h',
        'limit': 10
    })
    
    if klines:
        print(f"📈 Son {len(klines)} mum alındı")
        
        # Son mumun kapanış fiyatı
        last_close = float(klines[-1][4])
        print(f"🎯 Son kapanış fiyatı: {last_close}")
        
        # Chandelier Exit hesaplama (basit versiyon)
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        current_high = highs[-1]
        current_low = lows[-1]
        
        long_stop = max(highs) - (current_high - current_low) * 2.8
        short_stop = min(lows) + (current_high - current_low) * 2.8
        
        print(f"🟢 Long Stop: {long_stop:.2f}")
        print(f"🔴 Short Stop: {short_stop:.2f}")
        
        if last_close > long_stop:
            print("🎯 SİNYAL: BUY")
        elif last_close < short_stop:
            print("🎯 SİNYAL: SELL")
        else:
            print("🎯 SİNYAL: HOLD")
    
    print("\n" + "="*50)
    print("✅ Bot çalışması tamamlandı!")
    print("="*50)

if __name__ == "__main__":
    main()
