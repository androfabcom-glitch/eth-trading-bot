import os
import time
import hmac
import hashlib
import requests
from datetime import datetime

print("=== 🚀 ETH TRADING BOT BAŞLATILDI ===")
print(f"⏰ Zaman: {datetime.now()}")

# API Bilgileri
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = "https://testnet.binancefuture.com"

SYMBOL = "ETHUSDT"
LEVERAGE = 20

def make_request(endpoint, params=None, method='GET'):
    try:
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
        
        # Request gönder
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.post(url, data=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Hata: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 API Hatası: {e}")
        return None

def calculate_chandelier_TEST(klines):
    """TEST MOD: KESİN işlem yapsın diye"""
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines] 
    closes = [float(k[4]) for k in klines]
    
    current_close = closes[-1]
    
    # TEST: Mevcut fiyatın ÇOK YAKININA stop koy
    long_stop = current_close - 0.1  # 10 cent altı
    short_stop = current_close + 0.1  # 10 cent üstü
    
    print("🎯 TEST MODU AKTİF!")
    print(f"🟢 Long Stop: {long_stop:.2f}")
    print(f"🔴 Short Stop: {short_stop:.2f}")
    print(f"🎯 Current Price: {current_close:.2f}")
    
    # NORMAL mantık (fiyat > long_stop ise BUY)
    if current_close > long_stop:
        return "BUY", current_close
    elif current_close < short_stop:
        return "SELL", current_close
    else:
        return "HOLD", current_close

def execute_trade(signal, price, current_position):
    """Trading işlemini gerçekleştir"""
    balance_data = make_request('/fapi/v2/balance')
    usdt_balance = 0
    
    if balance_data:
        for asset in balance_data:
            if asset['asset'] == 'USDT':
                usdt_balance = float(asset['balance'])
                break
    
    if usdt_balance <= 0:
        print("❌ Yetersiz bakiye!")
        return
    
    # Miktar hesapla (%100 bakiye, 20x kaldıraç)
    quantity = (usdt_balance * 1.0) * LEVERAGE / price
    quantity = round(quantity, 3)
    
    print(f"💰 Bakiye: {usdt_balance} USDT")
    print(f"📦 Kullanılacak miktar: {quantity} ETH")
    
    if signal == "BUY" and current_position <= 0:
        print("🎯 BUY Sinyali - Long işlemi yapılıyor...")
        
        if current_position < 0:
            # Short pozisyonu kapat
            print("🔻 Short pozisyon kapatılıyor...")
            close_result = make_request('/fapi/v1/order', {
                'symbol': SYMBOL,
                'side': 'BUY',
                'type': 'MARKET',
                'quantity': abs(current_position)
            }, 'POST')
            if close_result:
                print("✅ Short pozisyon kapatıldı")
            time.sleep(1)
        
        # Long pozisyon aç
        result = make_request('/fapi/v1/order', {
            'symbol': SYMBOL,
            'side': 'BUY',
            'type': 'MARKET',
            'quantity': quantity
        }, 'POST')
        
        if result:
            print(f"✅ Long pozisyon açıldı: {quantity} ETH")
            print(f"📊 Order Detay: {result}")
        else:
            print("❌ Long pozisyon açılamadı")
    
    elif signal == "SELL" and current_position >= 0:
        print("🎯 SELL Sinyali - Short işlemi yapılıyor...")
        
        if current_position > 0:
            # Long pozisyonu kapat
            print("🔺 Long pozisyon kapatılıyor...")
            close_result = make_request('/fapi/v1/order', {
                'symbol': SYMBOL,
                'side': 'SELL',
                'type': 'MARKET',
                'quantity': abs(current_position)
            }, 'POST')
            if close_result:
                print("✅ Long pozisyon kapatıldı")
            time.sleep(1)
        
        # Short pozisyon aç
        result = make_request('/fapi/v1/order', {
            'symbol': SYMBOL,
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': quantity
        }, 'POST')
        
        if result:
            print(f"✅ Short pozisyon açıldı: {quantity} ETH")
            print(f"📊 Order Detay: {result}")
        else:
            print("❌ Short pozisyon açılamadı")
    
    else:
        print(f"⚪ İşlem yapılmadı - Sinyal: {signal}, Pozisyon: {current_position}")

def main():
    print("\n" + "="*50)
    print("🤖 ETH/USDT TRADING BOT - TEST MODU")
    print("="*50)
    print("🎯 BU veya SELL yapacak şekilde ayarlandı!")
    
    # 1. Mevcut pozisyonu kontrol et
    print("\n1️⃣ Pozisyon kontrol ediliyor...")
    positions = make_request('/fapi/v2/positionRisk', {'symbol': SYMBOL})
    current_position = 0
    
    if positions:
        for pos in positions:
            amount = float(pos.get('positionAmt', 0))
            if amount != 0:
                current_position = amount
                print(f"📊 Mevcut Pozisyon: {amount} ETH")
                break
    
    if current_position == 0:
        print("📭 Açık pozisyon yok")
    
    # 2. Mum verilerini al ve TEST sinyali hesapla
    print("\n2️⃣ TEST Sinyali hesaplanıyor...")
    klines = make_request('/fapi/v1/klines', {
        'symbol': SYMBOL,
        'interval': '1h',
        'limit': 10
    })
    
    if klines:
        signal, current_price = calculate_chandelier_TEST(klines)
        print(f"🎯 Sinyal: {signal}")
        
        # 3. Trading işlemini gerçekleştir
        print("\n3️⃣ TRADING İŞLEMİ BAŞLIYOR...")
        execute_trade(signal, current_price, current_position)
    else:
        print("❌ Mum verileri alınamadı")
    
    print("\n" + "="*50)
    print("✅ Bot çalışması tamamlandı!")
    print("="*50)

if __name__ == "__main__":
    main()
