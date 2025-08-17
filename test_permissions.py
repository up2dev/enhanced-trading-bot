#!/usr/bin/env python3
"""
Test des permissions API Binance
"""

import os
from binance import Client
from src.utils import load_json_config

def test_binance_permissions():
    print("🔍 Test des permissions Binance...")
    
    try:
        # Charger la config
        config = load_json_config('config/config.json')
        
        api_key = config['binance']['api_key']
        api_secret = config['binance']['api_secret']
        
        print(f"📋 API Key: {api_key[:8]}...")
        
        # Test client
        client = Client(api_key, api_secret, testnet=False)
        
        # Test 1: Informations du compte
        print("1️⃣ Test info compte...")
        account = client.get_account()
        print(f"✅ Status: {account.get('accountType', 'N/A')}")
        
        # Test 2: Permissions
        print("2️⃣ Test permissions...")
        permissions = account.get('permissions', [])
        print(f"📋 Permissions: {permissions}")
        
        # Test 3: Status API
        print("3️⃣ Test status API...")
        status = client.get_system_status()
        print(f"🌐 Status système: {status}")
        
        # Test 4: Restriction IP
        print("4️⃣ Test restrictions...")
        try:
            # Tentative de récupération des ordres (nécessite trading)
            orders = client.get_open_orders(limit=1)
            print("✅ Permissions de trading OK")
        except Exception as e:
            print(f"❌ Pas de permission trading: {e}")
            
            # Vérifier si c'est un problème d'IP
            if "IP" in str(e).upper():
                print("🚨 PROBLÈME D'IP DÉTECTÉ!")
                print("💡 Solution: Supprimer les restrictions IP sur Binance")
        
        # Test 5: IP publique
        print("5️⃣ Votre IP publique:")
        import requests
        ip = requests.get('https://ipecho.net/plain').text
        print(f"🌍 IP: {ip}")
        print(f"💡 Ajoutez cette IP dans Binance API Management")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        
        if "Invalid API-key" in str(e):
            print("🚨 CLÉ API INVALIDE!")
        elif "Signature" in str(e):
            print("🚨 PROBLÈME DE SIGNATURE!")
        elif "IP" in str(e).upper():
            print("🚨 RESTRICTION IP!")

if __name__ == "__main__":
    test_binance_permissions()
