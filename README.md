# 🤖 Enhanced Trading Bot

Bot de trading automatisé pour Binance optimisé pour Raspberry Pi avec gestion avancée des ordres OCO/LIMIT et monitoring intelligent.

## 📁 Structure du Projet

```
enhanced_trading_bot/
├── 🤖 run_bot.py              # Script principal du bot
├── 📊 smart_monitor.py        # 🆕 Système de monitoring hybride
├── 🔧 config/                 # Configuration
│   ├── config.json           # Paramètres trading, API & Telegram
│   ├── config.template.json  # Template de configuration
│   └── email_config.json     # Configuration email
├── 🧠 src/                    # Code source
│   ├── bot.py                # Bot principal
│   ├── trading_engine.py     # Moteur de trading
│   ├── binance_client.py     # Client API Binance
│   ├── database.py           # Gestionnaire base SQLite
│   ├── portfolio_manager.py  # Gestionnaire portefeuille
│   ├── indicators.py         # Indicateurs techniques
│   └── utils.py              # Utilitaires
├── 💾 db/                     # Base de données SQLite
├── 📊 logs/                   # Fichiers de logs
├── 🛠️ Scripts utilitaires
│   ├── cleanup_db.py         # Nettoyage base de données
│   ├── db_query.py           # Explorateur base de données
│   └── setup.sh              # Script d'installation
└── 🐍 venv/                   # Environnement virtuel Python
```

---

## 🚀 Installation et Configuration

### **Installation automatique (recommandée)**

```bash
# Cloner le repository
git clone https://github.com/up2dev/enhanced-trading-bot.git
cd enhanced-trading-bot

# Installation interactive
chmod +x setup.sh
./setup.sh
```

### **Configuration Binance + Telegram**

Éditez `config/config.json` avec vos clés API :

```json
{
  "binance": {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "testnet": false
  },
  "telegram": {
    "enabled": true,
    "bot_token": "your_bot_token",
    "chat_id": "your_chat_id"
  },
  "trading": {
    "base_currency": "USDC",
    "max_trade_amount": 165,
    "profit_percentage": 3.0
  },
  "cryptos": {
    "BTC": {"active": true, "symbol": "BTCUSDC"},
    "ETH": {"active": true, "symbol": "ETHUSDC"}
  }
}
```

**Permissions Binance :**
- ✅ **Enable Trading**
- ✅ **Enable Reading** 
- ❌ **Disable Withdrawals**

---

## 📊 Smart Monitor v2.2.2 - Système de Rapports Révolutionnaire

### **🆕 Nouveau système de monitoring unifié**

Le **Smart Monitor** remplace tous les anciens scripts de monitoring par une solution hybride **EMAIL + TELEGRAM** automatique.

#### **⚡ Fonctionnalités**

- **📧 Rapports email détaillés** quotidiens/hebdomadaires
- **📱 Notifications Telegram condensées** instantanées
- **💎 Holdings vs 💰 Profits garantis** (terminologie précise)
- **📈 ROI complet** incluant positions actives
- **🔄 Timestamps hybrides** (compatibilité maximale)
- **🚀 Ultra-optimisé** : 150 lignes vs 600+ ancien système

#### **📋 Usage**

```bash
# Rapport quotidien (automatique 18h)
python3 smart_monitor.py daily

# Rapport hebdomadaire (automatique dimanche 19h)
python3 smart_monitor.py weekly
```

#### **📊 Exemple de rapport quotidien**

```
🤖 TRADING BOT - Rapport Quotidien
📅 03/01/2025 18:00

💰 TRANSACTIONS AUJOURD'HUI
├─ 2 achats, 3 ventes
├─ Investi: 165.00 USDC
├─ Vendu: 245.30 USDC  
├─ Profit brut: +80.30 USDC
└─ 4 cryptos tradées

🎯 POSITIONS ACTIVES (8 ordres)
├─ 5 ordres OCO
├─ 3 ordres LIMIT
├─ 💎 Holdings: 125.30 USDC (3 ordres)
└─ 💰 Profits garantis: +67.45 USDC (5 ordres)

✅ SYSTÈME RASPBERRY PI
├─ CPU: 52°C
├─ RAM: 34%
└─ Disque: 12%
```

#### **📱 Exemple Telegram**

```
🤖 TRADING BOT - 03/01 18:00

💚 2B/3S → +80.30 USDC
🎯 8 ordres (💎125 + 💰+67)
✅ 52°C RAM 34%
```

#### **🔄 Migration depuis anciens scripts**

```bash
# Sauvegarder anciens scripts (optionnel)
mkdir -p backup_old_monitoring_v2.1.7
mv monitor.sh email_sender.py performance_stats.py backup_old_monitoring_v2.1.7/

# Le Smart Monitor est déjà en place !
python3 smart_monitor.py daily
```

#### **⚙️ Configuration automatique**

```bash
# Éditer le crontab
crontab -e

# NOUVEAU système simplifié (remplace toutes les anciennes lignes)
# Bot toutes les 10 minutes
*/10 * * * * /home/yotsi/enhanced_trading_bot/run_wrapper.sh

# Rapports automatiques EMAIL + TELEGRAM
0 18 * * * cd /home/yotsi/enhanced_trading_bot && python3 smart_monitor.py daily >> logs/monitor.log 2>&1
0 19 * * 0 cd /home/yotsi/enhanced_trading_bot && python3 smart_monitor.py weekly >> logs/monitor.log 2>&1
```

#### **🎯 Avantages Smart Monitor**

| Ancien système | Smart Monitor v2.2.2 |
|----------------|----------------------|
| ❌ 3 scripts (600+ lignes) | ✅ 1 script (150 lignes) |
| ❌ Parsing logs fragile | ✅ Stats directes DB |
| ❌ Email OU Telegram | ✅ Email ET Telegram |
| ❌ Stats incohérentes | ✅ Une source de vérité |
| ❌ Maintenance complexe | ✅ Maintenance simple |
| ❌ "Valeur totale" confuse | ✅ Holdings vs Profits clairs |

---

## 🎮 Utilisation des Scripts

### 🤖 **Bot Principal** (`run_bot.py`)

```bash
# Mode simulation (recommandé pour tests)
python3 run_bot.py --dry-run

# Mode réel
python3 run_bot.py

# Avec debug
python3 run_bot.py --log-level DEBUG
```

### 🗃️ **Explorateur de Base** (`db_query.py`)

```bash
# Vue d'ensemble
python3 db_query.py

# Mode interactif
python3 db_query.py --interactive

# Statistiques rapides
python3 db_query.py --stats
```

### 🧹 **Nettoyeur de Base** (`cleanup_db.py`)

```bash
# Mode interactif (recommandé)
python3 cleanup_db.py --interactive

# Garder seulement 30 jours
python3 cleanup_db.py --days-keep 30
```

---

## 📊 Configuration Trading

### **Stratégie RSI**
- **RSI < 35** : Premier achat possible
- **RSI < 30** : Deuxième achat possible
- **Profit cible** : 3% par défaut (configurable)
- **Stop-loss** : -8% (ordres OCO automatiques)

### **Gestion des risques**
- **Montant max par trade** : 165 USDC
- **Réserve minimale** : 21 USDC
- **Cooldown** : 20 minutes entre achats
- **Limite quotidienne** : 150 trades max

### **Holdings vs Profits garantis**

**💎 Holdings** : Cryptos mises de côté (`kept_quantity > 0`)
- Valeur estimée avec dernier prix connu
- Profit NON réalisé

**💰 Profits garantis** : Ordres sans kept_quantity 
- Toute la crypto sera revendue au prix cible
- Profit calculé = `prix_achat * quantité * (profit_target / 100)`

---

## 🛠️ Maintenance et Diagnostic

### **Vérification quotidienne**

```bash
# 1. Voir le rapport Smart Monitor
python3 smart_monitor.py daily

# 2. Consulter les positions actives
python3 db_query.py -i
# puis : show oco_orders 10

# 3. Vérifier les erreurs
tail -20 logs/trading_bot.log
```

### **Diagnostic en cas de problème**

```bash
# Test configuration
python3 run_bot.py --dry-run --log-level DEBUG

# Vérifier base de données
python3 db_query.py --stats

# Test Smart Monitor
python3 smart_monitor.py daily
```

---

## 🎯 Versions et Mises à Jour

### **📈 Dernières versions stables**

| Version | Date | Description |
|---------|------|-------------|
| **v2.1.8** | 2025-01 | Smart Monitor v2.2.2 - Rapports hybrides |
| **v2.1.7** | 2024-12 | Corrections timestamps Binance |
| **v1.2.4** | 2024-11 | Correction multi-fill orders (CRITIQUE) |

### **⚠️ Migration v2.1.8**

Si vous migrez depuis une version antérieure :

```bash
# 1. Mise à jour du code
git pull origin main

# 2. Le Smart Monitor remplace automatiquement :
# - monitor.sh ❌
# - email_sender.py ❌  
# - performance_stats.py ❌

# 3. Mettre à jour le crontab (voir section Smart Monitor)

# 4. Tester
python3 smart_monitor.py daily
```

---

## 🔗 Support

- **Repository GitHub** : [enhanced-trading-bot](https://github.com/up2dev/enhanced-trading-bot)
- **Issues** : [GitHub Issues](https://github.com/up2dev/enhanced-trading-bot/issues)
- **Releases** : [GitHub Releases](https://github.com/up2dev/enhanced-trading-bot/releases)

---

## 🏆 Fonctionnalités Principales

- ✅ **Trading RSI automatique** 14-périodes
- ✅ **Ordres OCO/LIMIT** avec stop-loss -8%
- ✅ **Gestion multi-fill** complète
- ✅ **Smart Monitor hybride** EMAIL + Telegram
- ✅ **Holdings vs Profits** (terminologie précise)
- ✅ **ROI complet** avec positions actives
- ✅ **Protection risques** (cooldown, limites)
- ✅ **Optimisé Raspberry Pi** Zero W2
- ✅ **Base SQLite robuste** avec cleanup auto
- ✅ **Mode simulation** complet

---

**🎯 Système complet prêt pour trading 24/7 avec surveillance automatique !**

**📊 Smart Monitor v2.2.2 : La révolution du monitoring crypto !**
```

## 🎯 **PRINCIPALES MODIFICATIONS**

### **✅ Ajouts v2.1.8**
- **📊 Section Smart Monitor complète** avec exemples
- **🔄 Guide de migration** depuis anciens scripts
- **📱 Exemples Telegram/Email** concrets
- **💎💰 Explication Holdings vs Profits** garantis
- **⚙️ Nouveau crontab simplifié**

### **❌ Suppressions obsolètes**
- Scripts monitor.sh, email_sender.py, performance_stats.py
- Configurations email complexes
- Rapports séparés multiples

### **🔧 Mises à jour**
- Structure projet actualisée
- Versions et historique des releases
- Procédures de maintenance simplifiées
- Guide troubleshooting adapté

**Ce README reflète maintenant parfaitement l'état v2.1.8 avec le Smart Monitor !** 🚀
