"""
Enhanced Trading Bot Dashboard - API Stats
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats')
def get_stats():
    """Statistiques générales du bot"""
    try:
        # Import ici pour éviter les erreurs circulaires
        from ..utils.data_provider import data_provider
        
        stats = data_provider.get_quick_stats()
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Erreur stats: {e}")
        return jsonify({
            'error': str(e),
            'daily_buys': 0,
            'active_oco': 0,
            'total_transactions': 0,
            'bot_status': 'error',
            'timestamp': datetime.now().isoformat()
        })

@stats_bp.route('/stats/transactions')
def get_recent_transactions():
    """Transactions récentes"""
    try:
        from ..utils.data_provider import data_provider
        
        # Paramètres optionnels
        limit = request.args.get('limit', default=20, type=int)
        period = request.args.get('period', default=None, type=str)
        
        transactions = data_provider.get_recent_transactions(limit=limit, period=period)
        return jsonify({
            'transactions': transactions
        })
        
    except Exception as e:
        print(f"❌ Erreur transactions: {e}")
        return jsonify({
            'transactions': [],
            'error': str(e)
        })
