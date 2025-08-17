# 🤖 Enhanced Trading Bot

Bot de trading automatisé pour Binance optimisé pour Raspberry Pi avec gestion avancée des ordres OCO et stop-loss.

## 📁 Structure du Projet

```
enhanced_trading_bot/
├── 🤖 run_bot.py              # Script principal du bot
├── 🔧 config/                 # Configuration
│   └── config.json           # Paramètres trading et API
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
│   ├── performance_stats.py  # Analyseur de performance
│   ├── monitor.sh            # Monitoring et rapports
│   └── run_wrapper.sh        # Wrapper d'exécution cron
└── 🐍 venv/                   # Environnement virtuel Python
```

---

## 🚀 Installation et Configuration

### 1. **Prérequis**

```bash
# Système à jour
sudo apt update && sudo apt upgrade -y

# Dépendances Python
sudo apt install python3-full python3-pip python3-venv -y
```

### 2. **Configuration**

```bash
# Aller dans le répertoire
cd /home/yotsi/enhanced_trading_bot

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier les dépendances
pip install -r requirements.txt
```

### 3. **Configuration Binance**

Éditez `config/config.json` avec vos clés API et configurez les permissions sur Binance :

- ✅ **Enable Trading**
- ✅ **Enable Reading** 
- ❌ **Disable Withdrawals**

---

## 🎮 Utilisation des Scripts

### 🤖 **Bot Principal** (`run_bot.py`)

**Script principal de trading automatisé**

```bash
# Mode simulation (recommandé pour tests)
python3 run_bot.py --dry-run

# Mode réel (attention !)
python3 run_bot.py

# Avec niveau de logs spécifique
python3 run_bot.py --log-level DEBUG

# Aide complète
python3 run_bot.py --help
```

**Options disponibles :**
- `--dry-run` : Mode simulation (aucun ordre réel)
- `--log-level` : Niveau de logs (DEBUG, INFO, WARNING, ERROR)
- `--config` : Chemin vers fichier de config custom

---

### 🗃️ **Explorateur de Base** (`db_query.py`)

**Outil interactif pour consulter la base de données**

```bash
# Vue d'ensemble
python3 db_query.py

# Statistiques rapides
python3 db_query.py --stats

# Afficher une table spécifique
python3 db_query.py --table transactions --limit 20

# Mode interactif (recommandé)
python3 db_query.py --interactive

# Recherche de transactions
python3 db_query.py --search BTC --days 7
```

**Commandes mode interactif :**
```
db> list                    # Lister les tables
db> show transactions 10    # Afficher 10 transactions
db> struct oco_orders      # Structure d'une table
db> stats                  # Statistiques rapides
db> search BTC 7           # Transactions BTC 7 jours
db> sql SELECT * FROM transactions LIMIT 5
db> quit                   # Quitter
```

---

### 📊 **Analyseur de Performance** (`performance_stats.py`)

**Analyse complète ROI, profits, statistiques**

```bash
# Analyse des 30 derniers jours
python3 performance_stats.py

# Rapport complet
python3 performance_stats.py --full

# Analyse d'une crypto spécifique
python3 performance_stats.py --symbol BTC --days 7

# Export vers fichier
python3 performance_stats.py --export rapport.txt --full

# Période personnalisée
python3 performance_stats.py --days 90 --full
```

**Informations fournies :**
- ROI global et par crypto
- Profits/pertes détaillés
- Performance mensuelle
- Statistiques des ordres OCO
- Fréquence de trading

---

### 🧹 **Nettoyeur de Base** (`cleanup_db.py`)

**Nettoyage et maintenance de la base de données**

```bash
# Mode interactif (recommandé)
python3 cleanup_db.py --interactive

# Nettoyer données orphelines (cas spécifique transactions sans OCO)
python3 cleanup_db.py --clear-orphaned

# Supprimer toutes les données (⚠️ ATTENTION)
python3 cleanup_db.py --clear-all

# Garder seulement les 7 derniers jours
python3 cleanup_db.py --days-keep 7
```

⚠️ **SAUVEGARDE AUTOMATIQUE** : Chaque nettoyage crée une sauvegarde dans `db/`

---

### 📈 **Monitoring** (`monitor.sh`)

**Rapport quotidien automatique du système**

```bash
# Générer rapport maintenant
./monitor.sh

# Voir le dernier rapport
cat logs/daily_report.log
```

**Contenu du rapport :**
- Statistiques d'exécution du bot
- Activité de trading
- Performance système Raspberry Pi
- Erreurs récentes
- Diagnostic santé

---

### 📧 **Système Email** (`email_sender.py`)

**Envoi automatique des rapports par email**

#### **Configuration initiale :**

```bash
# Créer la configuration depuis le template
python3 email_sender.py --test

# Éditer la configuration avec vos paramètres
nano config/email_config.json

---

### 🔄 **Wrapper Cron** (`run_wrapper.sh`)

**Script d'exécution automatique via cron**

```bash
# Test manuel
./run_wrapper.sh

# Voir les logs cron
tail -20 logs/cron.log
```

---

## ⚙️ Configuration Cron (Automatisation)

### **Installation des tâches automatiques :**

```bash
# Éditer le cron
crontab -e

# Ajouter ces lignes :
# Bot toutes les 10 minutes
*/10 * * * * /home/yotsi/enhanced_trading_bot/run_wrapper.sh

# Rapport quotidien à 23h
0 23 * * * /home/yotsi/enhanced_trading_bot/monitor.sh
```

### **Vérification cron :**

```bash
# Voir les tâches actives
crontab -l

# Logs système cron
sudo tail /var/log/syslog | grep CRON
```

---

## 📊 Configuration

### **`config/config.json`** - Configuration principale

```json
{
  "binance": {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "testnet": false
  },
  "trading": {
    "max_trade_amount": 165,
    "max_trade_ratio": 0.25,
    "min_balance_reserve": 21,
    "rsi_period": 14,
    "timeframe": "1h",
    "first_rsi_rate": 35,
    "second_rsi_rate": 30
  },
  "risk_management": {
    "max_positions_per_crypto": 15,
    "cooldown_minutes": 20,
    "max_daily_trades": 150,
    "stop_loss_percentage": -8.0,
    "use_oco_orders": true
  },
  "cryptos": {
    "BTC": {
      "active": true,
      "symbol": "BTCUSDC",
      "profit_percentage": 3.0,
      "max_allocation": 0.24
    },
    "ETH": {
      "active": true,
      "symbol": "ETHUSDC", 
      "profit_percentage": 2.5,
      "max_allocation": 0.19
    }
  }
}
```

---

## 📁 Gestion des Logs

### **Fichiers de logs :**
- `logs/trading_bot.log` : Activité principale du bot
- `logs/cron.log` : Exécutions automatiques
- `logs/errors.log` : Erreurs système
- `logs/daily_report.log` : Rapport quotidien

### **Consultation des logs :**

```bash
# Logs en temps réel
tail -f logs/trading_bot.log

# Dernières erreurs
tail -20 logs/errors.log

# Activité cron
grep "$(date +%Y-%m-%d)" logs/cron.log

# Statistiques du jour
grep "STATISTIQUES" logs/daily_report.log
```

---

## 🛠️ Maintenance

### **Mise à jour du système :**

```bash
# Sauvegardes
cp db/trading.db db/backup_$(date +%Y%m%d).db

# Nettoyage périodique
python3 cleanup_db.py --days-keep 30

# Rotation des logs (automatique mais peut être forcée)
find logs/ -name "*.log" -mtime +15 -delete
```

### **Diagnostic en cas de problème :**

```bash
# 1. Vérifier les permissions API
python3 test_permissions.py

# 2. Tester la configuration
python3 run_bot.py --dry-run --log-level DEBUG

# 3. Vérifier la base de données
python3 db_query.py --stats

# 4. Analyser les performances
python3 performance_stats.py

# 5. Voir le rapport système
./monitor.sh && cat logs/daily_report.log
```

---

## 🚨 Résolution de Problèmes

### **Bot ne démarre pas :**

```bash
# Vérifier l'environnement
source venv/bin/activate
python3 --version
pip list

# Tester la config
python3 -c "import json; print('Config OK' if json.load(open('config/config.json')) else 'Erreur')"
```

### **Pas de trading :**

```bash
# Vérifier les permissions Binance
python3 test_permissions.py

# Voir les raisons dans les logs
grep "Pas d'achat" logs/trading_bot.log | tail -10
```

### **Erreurs de base de données :**

```bash
# Diagnostic complet
python3 db_query.py --stats

# Nettoyage si nécessaire
python3 cleanup_db.py --clear-orphaned
```

---

## 📞 Support et Développement

### **Structure du code :**
- `src/bot.py` : Logique principale
- `src/trading_engine.py` : Décisions de trading (RSI, OCO)
- `src/binance_client.py` : Interface API Binance
- `src/database.py` : Gestion SQLite
- `src/portfolio_manager.py` : Gestion allocation

### **Personnalisation :**
- Modifier `config.json` pour ajuster les paramètres
- Les seuils RSI sont dans la section `trading`
- Les allocations par crypto dans `cryptos`
- Les sécurités dans `risk_management`

### **Logs de développement :**

```bash
# Debug complet
python3 run_bot.py --dry-run --log-level DEBUG > debug.log 2>&1

# Analyser les indicateurs techniques
grep "Indicateurs" logs/trading_bot.log
```

---

## 🏆 Fonctionnalités Avancées

- ✅ **Trading RSI automatique** avec gestion des rachats
- ✅ **Ordres OCO** (profit + stop-loss) avec surveillance
- ✅ **Gestion d'allocation portfolio** intelligente
- ✅ **Protection cooldown** et limites journalières
- ✅ **Monitoring système** complet Raspberry Pi
- ✅ **Statistiques de performance** détaillées
- ✅ **Gestion des erreurs** robuste avec retry
- ✅ **Mode simulation** complet pour tests

---

## 🎯 Utilisation Quotidienne

### **Routine de vérification quotidienne :**

```bash
# 1. Voir le rapport quotidien
cat logs/daily_report.log

# 2. Vérifier les performances
python3 performance_stats.py

# 3. Consulter l'activité récente
python3 db_query.py --interactive
# puis : search ALL 1

# 4. Vérifier les ordres OCO actifs
python3 db_query.py -i
# puis : show oco_orders 10
```

### **Commandes de maintenance hebdomadaire :**

```bash
# Nettoyage des données anciennes (optionnel)
python3 cleanup_db.py --days-keep 30

# Vérification santé système
./monitor.sh

# Export rapport performance
python3 performance_stats.py --export weekly_report.txt --full
```

---

**🎯 Le bot est conçu pour fonctionner 24/7 sur Raspberry Pi avec une surveillance minimale !**

Pour toute question spécifique, consultez les logs ou utilisez les outils de diagnostic intégrés.
```
