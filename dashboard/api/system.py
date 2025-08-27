"""
Enhanced Trading Bot Dashboard - Endpoints système
"""

from flask import Blueprint, jsonify
from datetime import datetime

system_bp = Blueprint('system', __name__)

@system_bp.route('/health')
def health_check():
    """Vérification de santé du service"""
    return jsonify({
        'status': 'ok',
        'service': 'Enhanced Trading Bot Dashboard',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })
