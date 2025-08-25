#!/usr/bin/env python3
"""
Test récupération balances réelles depuis Binance
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.binance_client import EnhancedBinanceClient
from src.portfolio_manager import EnhancedPortfolioManager

def get_real_balances():
    pm = EnhancedPortfolioManager('config/config.json')
    binance_config = pm.get_binance_config()
    client = EnhancedBinanceClient(binance_config['api_key'], binance_config['api_secret'])
    
    try:
        # Récupérer balances compte
        account = client._make_request_with_retry(
            client.client.get_account
        )
        
        print("💰 BALANCES RÉELLES:")
        
        balances = account['balances']
        for balance in balances:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                print(f"   {asset}: {total:.8f} (libre: {free:.8f}, bloqué: {locked:.8f})")
        
        print(f"\n📊 Total assets avec balance: {len([b for b in balances if float(b['free']) + float(b['locked']) > 0])}")
        
        # Test prix actuels
        print(f"\n💱 PRIX ACTUELS:")
        symbols = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC']
        for symbol in symbols:
            try:
                ticker = client._make_request_with_retry(
                    client.client.get_symbol_ticker,
                    symbol=symbol
                )
                print(f"   {symbol}: {float(ticker['price']):.6f} USDC")
            except:
                print(f"   {symbol}: Erreur récupération prix")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    get_real_balances()
