"""
Enhanced Trading Bot Dashboard - Application Flask
"""

from flask import Flask, render_template, jsonify
import os
import sys
from pathlib import Path

# Ajouter le dossier racine pour accès aux modules src
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

def create_app():
    """Factory pour créer l'app Flask"""
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'trading-bot-dashboard-2024'
    
    # Import des modules API
    from .api.stats import stats_bp
    from .api.portfolio import portfolio_bp  
    from .api.orders import orders_bp
    from .api.system import system_bp
    
    # Enregistrement des blueprints API
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(portfolio_bp, url_prefix='/api')
    app.register_blueprint(orders_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api')
    
    # Routes principales
    @app.route('/')
    def index():
        """Page d'accueil du dashboard"""
        return render_template('index.html')
    
    @app.route('/portfolio')
    def portfolio_page():
        """Page portefeuille détaillé"""
        return render_template('portfolio.html')
    
    @app.route('/orders')
    def orders_page():
        """Page ordres OCO"""
        return render_template('orders.html')
    
    @app.route('/transactions')
    def transactions_page():
        """Page transactions"""
        return render_template('transactions.html')
    
    return app
