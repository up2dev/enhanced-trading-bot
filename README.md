## 🤖 Enhanced Trading Bot (Raspberry Pi & Linux)

Bot de trading automatisé pour Binance, optimisé pour Raspberry Pi Zero W2, avec OCO (take profit + stop‑loss), gestion des multi‑fills, limites de risque, et outils d’observabilité (logs, monitoring, rapports e‑mail, statistiques de performance).

---

### 📁 Structure du projet

```
enhanced-trading-bot/
├── run_bot.py                 # Entrée principale
├── src/                       # Code source
│   ├── bot.py                 # Orchestration bot + cycle trading
│   ├── trading_engine.py      # Logique trading (RSI, OCO, multi-fill, sécurité)
│   ├── binance_client.py      # Client Binance + retries + cache
│   ├── database.py            # SQLite (transactions + oco_orders)
│   ├── portfolio_manager.py   # Chargement/validation config + allocations
│   ├── indicators.py          # Indicateurs techniques (RSI, MACD, BB, etc.)
│   └── utils.py               # Logging, système, helpers Raspberry Pi
├── config/
│   ├── config.template.json   # Modèle de configuration principale
│   └── email_config.template.json  # Modèle configuration e‑mail
├── db/                        # Base SQLite (ignorée par Git)
├── logs/                      # Logs (rotation/archivage)
├── scripts & outils
│   ├── run_wrapper.sh         # Wrapper cron exécution bot
│   ├── monitor.sh             # Rapport quotidien + santé système
│   ├── setup.sh               # Installation guidée (Pi/Linux)
│   ├── update.sh              # Mise à jour + sauvegardes
│   ├── db_query.py            # Explorateur DB interactif
│   ├── performance_stats.py   # Statistiques de performance (ROI, OCO…)
│   ├── email_sender.py        # Envoi e‑mails quotidiens/hebdo
│   ├── migrate_db.py          # Migration DB avec préservation des données
│   └── test_permissions.py    # Test rapide des permissions Binance
└── requirements.txt
```

---

### 🚀 Installation

#### Pré‑requis
- Linux / Raspberry Pi OS / WSL (Windows Subsystem for Linux)
- Python 3.9+ (recommandé), `pip`, `venv`
- Outils système: `git`, `sqlite3`, `curl` (pour `monitor.sh`), `bc` (optionnel mais utile)

#### Méthode 1 — Installation guidée (recommandée)
```bash
# Cloner
git clone https://github.com/up2dev/enhanced-trading-bot.git
cd enhanced-trading-bot

# Rendre les scripts exécutables
chmod +x setup.sh update.sh run_wrapper.sh monitor.sh

# Lancer l’installation guidée (choix 1 recommandé)
./setup.sh
```
Cette procédure crée un venv, installe les dépendances Python, prépare les répertoires (`logs`, `db`, `config`) et copie les templates de configuration.

#### Méthode 2 — Installation manuelle
```bash
# Paquets système
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-full python3-pip python3-venv git sqlite3 curl

# Environnement Python
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Configuration
mkdir -p logs db config
cp config/config.template.json config/config.json
# Éditez config/config.json et ajoutez vos clés API Binance
```

WSL (Windows): exécutez ces commandes dans un terminal WSL (Ubuntu). Les scripts `.sh` fonctionnent sous WSL.

---

### 🔐 Configuration

- Fichier principal: `config/config.json` (copié depuis `config/config.template.json`).
- Les clés API peuvent être injectées via variables d’environnement (plus sûr):
```bash
export BINANCE_API_KEY="votre_api_key"
export BINANCE_API_SECRET="votre_api_secret"
```
Le `PortfolioManager` injecte automatiquement ces variables si présentes.

Sections clés de `config.json`:
- `binance`: `api_key`, `api_secret`, `testnet`
- `trading`: devise de base, tailles max de trade, période RSI, timeframe, seuils RSI
- `risk_management`: limites sécurité (positions max/crypto, cooldown, stop_loss, OCO)
- `advanced_strategy`: `future_transfer_enabled` (logique “récupérer l’investissement initial”)
- `cryptos`: liste des actifs, symbole, allocation max et cible de profit par crypto

Git ignore `config/config.json`, DB, logs par sécurité et propreté.

---

### ▶️ Lancer le bot

Dans le venv:
```bash
# Mode simulation (aucun ordre réel)
python3 run_bot.py --dry-run

# Mode réel (attention!)
python3 run_bot.py

# Ajuster le niveau de logs
python3 run_bot.py --dry-run --log-level DEBUG

# Utiliser un fichier de config spécifique
python3 run_bot.py --config config/config.json
```

Comportement clé:
- Connexion API testée au démarrage, synchronisation du timestamp.
- Cycle de trading unique par exécution: vérifications, stats, décision RSI, achat éventuel, placement OCO (ou fallback limite), monitoring OCO.
- Logs détaillés dans `logs/trading_bot.log` + `logs/errors.log`.

---

### 🧠 Stratégie et sécurités

- Signal d’achat: basés sur RSI (configurable), avec journalisation informative des autres indicateurs (MACD, Bollinger, Stochastic, ADX, etc.).
- Sécurités:
  - Cooldown persistant entre ordres par symbole (via DB, timestamps Binance en millisecondes gérés correctement).
  - Limite journalière globale des achats.
  - Comptage des “positions logiques” par symbole (OCO dédiés via `orderListId` + ordres LIMIT simples).
- Ventes:
  - OCO réel quand possible: LIMIT_MAKER (take profit) + STOP_LOSS_LIMIT (stop‑loss).
  - Fallback en LIMIT si OCO indisponible.
  - Mode “récupérer l’investissement initial” avec `kept_quantity` conservée.

---

### 💾 Base de données (SQLite)

- Fichier: `db/trading.db` (créé automatiquement).
- Tables essentielles:
  - `transactions`: toutes les transactions (BUY/SELL), gère correctement les multi‑fills (quantité/prix moyens et commissions agrégées).
  - `oco_orders`: OCO actifs et historiques, IDs liés (profit, stop), quantités gardées, exécutions et statuts.
- Index optimisés pour les requêtes utilisées.

Outils utiles:
```bash
# Explorateur DB (vue, stats, requêtes, mode interactif)
python3 db_query.py --interactive

# Migration DB (préserve les données)
python3 migrate_db.py
```

---

### 📊 Statistiques et rapports

- `performance_stats.py`: ROI, profits/pertes, OCO, fréquence, répartition par crypto.
```bash
# Analyse 30 jours
python3 performance_stats.py

# Rapport complet
python3 performance_stats.py --full

# Crypto spécifique
python3 performance_stats.py --symbol BTC --days 7

# Export vers fichier
python3 performance_stats.py --export rapport.txt --full
```

- `monitor.sh`: génère un rapport quotidien consolidé `logs/daily_report.log` (exécutions cron, trading, erreurs, santé système, disque/mémoire, prochaine exécution estimée).
```bash
./monitor.sh
cat logs/daily_report.log
```

- `email_sender.py`: envoi d’e‑mails (quotidien/hebdo) avec intégration du monitoring et performance.
```bash
# Créer/valider la config e‑mail
python3 email_sender.py --test

# Quotidien
python3 email_sender.py --daily

# Hebdomadaire (inclut export performance)
python3 email_sender.py --weekly
```
Configurer `config/email_config.json` à partir du template. Pour Gmail, utilisez un “mot de passe d’application” (2FA activée).

---

### ⏱️ Automatisation (cron)

Exemples pour Linux/Pi (adapter le chemin d’installation):
```bash
crontab -e
# Toutes les 10 minutes: exécuter le bot via wrapper
*/10 * * * * /home/yotsi/enhanced_trading_bot/run_wrapper.sh
# Rapport quotidien à 23h
0 23 * * * /home/yotsi/enhanced_trading_bot/monitor.sh
```
`run_wrapper.sh` vérifie le venv, la connectivité, journalise dans `logs/cron.log`, et mesure la durée d’exécution.

Sous WSL, cron n’est pas actif par défaut. Utilisez `systemd` sous WSLg, un planificateur Windows, ou lancez manuellement.

---

### 🔄 Mise à jour du projet

```bash
# Sauvegarde configuration et DB, pull Git, mise à jour deps, permissions
./update.sh

# Vérifier rapidement ensuite
python3 run_bot.py --dry-run --log-level INFO
```

---

### 🧩 Dépendances

`requirements.txt` (extrait):
- `python-binance==1.0.19`
- `pandas>=2.0.0`, `pandas-ta>=0.3.14b0`, `numpy>=1.24.0`
- `requests>=2.31.0`, `cryptography>=41.0.0`, `aiohttp>=3.8.0`

---

### ✅ Points critiques corrigés (importants)

- Multi‑fills achat: agrégation correcte quantité/prix/commission et insertion DB unique → OCO sur la quantité réelle (voir logs “RÉCAPITULATIF … fills”).
- Timestamps Binance en millisecondes: conversions corrigées pour tous les comptages (achats du jour, cooldown, stats).
- Extraction des IDs OCO: lecture via `orderReports` (types LIMIT_MAKER/STOP_LOSS_LIMIT), insertion DB robuste.
- Position logique: comptage par `orderListId` (OCO) + LIMIT simples pour refléter la réalité.

---

### 🔎 Dépannage rapide

- Vérifier l’installation Python/venv
```bash
source venv/bin/activate
python3 --version
pip list | grep binance
```
- Vérifier la configuration
```bash
python3 -c "import json; print('OK' if json.load(open('config/config.json')) else 'NOK')"
```
- Tester les permissions Binance
```bash
python3 test_permissions.py
```
- Lancer en DEBUG et inspecter
```bash
python3 run_bot.py --dry-run --log-level DEBUG
 tail -n 200 -f logs/trading_bot.log
```
- Vérifier la base
```bash
python3 db_query.py --stats
```
- Monitoring et erreurs
```bash
./monitor.sh && tail -n 50 logs/errors.log
```

Erreurs fréquentes:
- “Invalid API-key” → clé erronée / mauvais compte (testnet vs live).
- “Signature …” → secret invalide.
- “IP … restricted” → autorisez l’IP (voir `test_permissions.py`).
- “-1104” sur OCO → corrigé par l’implémentation actuelle.

---

### 🔒 Sécurité
- Ne jamais commiter `config/config.json`, DB, logs (déjà ignorés par `.gitignore`).
- Préférer les variables d’environnement pour les clés API.
- Désactiver les retraits sur la clé API. Activer “Enable Reading” et “Enable Trading” uniquement.
- Conserver le système à jour (`apt`, `pip`).

---

### ❓ FAQ
- Le bot passe‑t‑il plusieurs cycles par exécution ?
  - Non. Un cycle par exécution. Utilisez cron pour une exécution périodique.
- Puis‑je utiliser USDT au lieu de USDC ?
  - Oui, ajustez `base_currency` et les `symbol` correspondants.
- Comment limiter l’exposition par crypto ?
  - Via `max_allocation` par crypto et `max_trade_amount`/`max_trade_ratio` globaux.
- Comment activer uniquement certains actifs ?
  - Mettre `active: true/false` par actif dans `cryptos`.
- Mode testnet ?
  - `binance.testnet: true` + clés testnet.

---

### 🧪 Développement
- Code structuré, logs riches (console + fichiers avec rotation), utils spécifiques Raspberry Pi (réduction mémoire, lecture températures/charge).
- Style: typosafe, validations config, erreurs gérées, retries côté Binance.
- Contributions: PR/Issues bienvenues.

Liens utiles:
- Documentation Binance: [Binance API Docs](https://binance-docs.github.io/apidocs/spot/en/) 
- Repository GitHub: `https://github.com/up2dev/enhanced-trading-bot`

---

### 🏁 Résumé d’utilisation
- Installer (guidé ou manuel), configurer `config/config.json`, tester en `--dry-run`, planifier via cron, surveiller `logs/` et rapports, tenir le système et le repo à jour (`update.sh`).
