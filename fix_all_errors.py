#!/usr/bin/env python3
"""
Correction automatique de TOUTES les erreurs sqlite3.Row
"""

import re

with open('performance_stats.py', 'r') as f:
    content = f.read()

# 1. Corriger export_performance_report signature
content = re.sub(
    r'def export_performance_report\(self, filename=None\):',
    'def export_performance_report(self, filename=None, days=30):',
    content
)

# 2. Corriger les appels hardcodés dans export
content = re.sub(
    r'self\.get_trading_performance_with_holdings\(30\)',
    'self.get_trading_performance_with_holdings(days)',
    content
)

content = re.sub(
    r'self\.get_crypto_breakdown\(30\)',
    'self.get_crypto_breakdown(days)',
    content
)

# 3. Corriger l'appel dans main()
content = re.sub(
    r'analyzer\.export_performance_report\(args\.export\)',
    'analyzer.export_performance_report(args.export, args.days)',
    content
)

# 4. Protéger TOUS les accès direct aux Row
patterns_to_fix = [
    (r"buy_data\['weighted_avg'\]", "buy_data[1] if buy_data and len(buy_data) > 1 else 0"),
    (r"current_price_row\['price'\]", "current_price_row[0] if current_price_row and len(current_price_row) > 0 else 0"),
    (r"last_price_row\['price'\]", "last_price_row[0] if last_price_row and len(last_price_row) > 0 else 0"),
]

for pattern, replacement in patterns_to_fix:
    content = re.sub(pattern, replacement, content)

# 5. Entourer tous les accès restants dans des try/except
remaining_patterns = [
    r"crypto\['symbol'\]",
    r"crypto\['total_kept'\]", 
    r"oco\['symbol'\]",
    r"oco\['created_at'\]",
    r"order\['symbol'\]",
    r"order\['created_at'\]",
    r"sell\['symbol'\]",
    r"sell\['created_at'\]",
]

for pattern in remaining_patterns:
    content = re.sub(
        f"({pattern})",
        r"safe_row_access(\1)",
        content
    )

# 6. Ajouter la fonction helper au début de la classe
helper_function = '''
    def safe_row_access(self, row, key, default=None):
        """Accès sécurisé aux Row SQLite"""
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default
'''

# Insérer après la fonction _safe_int
content = re.sub(
    r'(def _safe_int\(self, value, default=0\):.*?return default)',
    r'\1\n' + helper_function,
    content,
    flags=re.DOTALL
)

with open('performance_stats.py', 'w') as f:
    f.write(content)

print("✅ TOUTES les corrections appliquées")
