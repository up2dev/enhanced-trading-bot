"""
Enhanced Trading Bot Dashboard - API Portfolio
"""

from flask import Blueprint, jsonify
from ..utils.data_provider import data_provider

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolio')
def get_portfolio():
    """Informations du portefeuille avec VRAIES données Binance"""
    try:
        portfolio_data = data_provider.get_portfolio_summary()
        return jsonify(portfolio_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/performance')
def get_portfolio_performance():
    """Performances du portefeuille"""
    try:
        return jsonify(data_provider.get_portfolio_performance())
        
    except Exception as e:
        return jsonify({
            'today': 0,
            '7d': 0,
            '30d': 0,
            'total': 0,
            'error': str(e)
        }), 500
