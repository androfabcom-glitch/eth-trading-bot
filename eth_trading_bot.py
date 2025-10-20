import os
import time
import hmac
import hashlib
import requests
from datetime import datetime
# TEST İÇİN - normal kodun üstüne ekle
def calculate_chandelier(klines):
    """TEST MOD: Mevcut fiyata yakın stoplar"""
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines] 
    closes = [float(k[4]) for k in klines]
    
    current_close = closes[-1]
    
    # TEST: Mevcut fiyatın hemen üstü/altı
    long_stop = current_close - 1  # ALTI
    short_stop = current_close + 1  # ÜSTÜ
    
    print(f"🟢 Long Stop: {long_stop:.2f}")
    print(f"🔴 Short Stop: {short_stop:.2f}")
    print(f"🎯 Current Price: {current_close:.2f}")
    
    # TERS mantık (test için)
    if current_close > short_stop:
        return "BUY", current_close
    elif current_close < long_stop:
        return "SELL", current_close
    else:
        return "HOLD", current_close
print("=== 🚀 ETH TRADING BOT BAŞLATILDI ===")
print(f"⏰ Zaman: {datetime.now()}")

# API Bilgileri
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
BASE_URL = "https://testnet.binancefuture.com"

SYMBOL = "ETHUSDT"
LEVERAGE = 20
ATR_PERIOD = 1
MULTIPLIER = 2.8

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

def calculate_chandelier(klines):
    """DOĞRU Chandelier Exit hesaplama"""
    if not klines or len(klines) < 2:
        return "HOLD", 0
    
    try:
        highs = [float(k[2]) for k in klines]  # High prices
        lows = [float(k[3]) for k in klines]   # Low prices
        closes = [float(k[4]) for k in klines] # Close prices
        
        current_high = highs[-1]
        current_low = lows[-1]
        current_close = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else closes[0]
        
        print(f"📊 Veri Aralığı: {len(klines)} mum")
        print(f"📈 En Yüksek: {max(highs):.2f}, En Düşük: {min(lows):.2f}")
        print(f"🎯 Mevcut Kapanış: {current_close:.2f}")
        
        # ATR Hesaplama (Period 1)
        tr = max(
            current_high - current_low,
            abs(current_high - prev_close),
            abs(current_low - prev_close)
        )
        atr = tr
        
        print(f"📏 ATR: {atr:.2f}")
        
        # DOĞRU Chandelier Exit formülü
        long_stop = max(highs) - (atr * MULTIPLIER)
        short_stop = min(lows) + (atr * MULTIPLIER)
        
        print(f"🟢 Long Stop: {long_stop:.2f}")
        print(f"🔴 Short Stop: {short_stop:.2f}")
        print(f"🎯 Current Price: {current_close:.2f}")
        
        # Sinyal belirleme
        if current_close > long_stop:
            signal = "BUY"
        elif current_close < short_stop:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        return signal, current_close
        
    except Exception as e:
        print(f"💥 Chandelier hesaplama hatası: {e}")
        return "HOLD", 0

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
        else:
            print("❌ Short pozisyon açılamadı")
    
    else:
        print(f"⚪ İşlem yapılmadı - Sinyal: {signal}, Pozisyon: {current_position}")

def main():
    print("\n" + "="*50)
    print("🤖 ETH/USDT TRADING BOT ÇALIŞIYOR")
    print("="*50)
    print(f"🎯 Strateji: Chandelier Exit (ATR:{ATR_PERIOD}, Multiplier:{MULTIPLIER})")
    
    # 1. Kaldıraç ayarla
    print("\n1️⃣ Kaldıraç ayarlanıyor...")
    leverage_result = make_request('/fapi/v1/leverage', {
        'symbol': SYMBOL,
        'leverage': LEVERAGE
    }, 'POST')
    
    if leverage_result:
        print(f"⚡ Kaldıraç {LEVERAGE}x ayarlandı")
    else:
        print("❌ Kaldıraç ayarlanamadı - API Key hatası?")
    
    # 2. Mevcut pozisyonu kontrol et
    print("\n2️⃣ Pozisyon kontrol ediliyor...")
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
    
    # 3. Mum verilerini al ve sinyal hesapla
    print("\n3️⃣ Sinyal hesaplanıyor...")
    klines = make_request('/fapi/v1/klines', {
        'symbol': SYMBOL,
        'interval': '1h',
        'limit': 22  # Daha fazla veri
    })
    
    if klines:
        signal, current_price = calculate_chandelier(klines)
        print(f"🎯 Sinyal: {signal}")
        
        # 4. Trading işlemini gerçekleştir
        print("\n4️⃣ Trading işlemi...")
        execute_trade(signal, current_price, current_position)
    else:
        print("❌ Mum verileri alınamadı")
    
    print("\n" + "="*50)
    print("✅ Bot çalışması tamamlandı!")
    print("="*50)

if __name__ == "__main__":
    main()
