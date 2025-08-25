"""
Enhanced Trading Bot Dashboard - API Orders
"""

from flask import Blueprint, jsonify
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
def get_orders():
    """Ordres OCO actifs"""
    try:
        from ..utils.data_provider import data_provider
        
        orders = data_provider.get_active_orders()
        return jsonify({
            'orders': orders
        })
        
    except Exception as e:
        print(f"❌ Erreur orders: {e}")
        return jsonify({
            'orders': [],
            'error': str(e)
        })

@orders_bp.route('/orders/history')
def get_orders_history():
    """Historique des ordres"""
    try:
        from ..utils.data_provider import data_provider
        history = data_provider.get_orders_history(limit=100)
        return jsonify({
            'orders': history
        })
        
    except Exception as e:
        return jsonify({
            'orders': [],
            'error': str(e)
        })
