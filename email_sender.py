#!/usr/bin/env python3
"""
Enhanced Trading Bot - Système d'envoi d'emails
Envoi automatique des rapports de monitoring et de performance
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json
import logging
import argparse

class TradingBotMailer:
    def __init__(self, config_path="config/email_config.json"):
        self.config_path = config_path
        self.template_path = "config/email_config.template.json"
        self.logger = logging.getLogger(__name__)
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/email.log'),
                logging.StreamHandler()
            ]
        )
        
        self.config = self._load_email_config()
    
    def _load_email_config(self):
        """Charge la configuration email avec gestion des templates"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"✅ Configuration email chargée: {self.config_path}")
                    return config
            else:
                self.logger.warning(f"⚠️  Configuration email non trouvée: {self.config_path}")
                return self._create_config_from_template()
                
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement config email: {e}")
            return self._create_config_from_template()
    
    def _create_config_from_template(self):
        """Crée la config depuis le template"""
        try:
            if os.path.exists(self.template_path):
                # Copier le template
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    template_config = json.load(f)
                
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(template_config, f, indent=2, ensure_ascii=False)
                
                print(f"📧 Configuration email créée depuis template: {self.config_path}")
                print("⚠️  IMPORTANT: Éditez ce fichier avec vos vrais paramètres SMTP")
                print("🔧 Guide Gmail: https://support.google.com/accounts/answer/185833")
                
                return template_config
            else:
                self.logger.error(f"❌ Template non trouvé: {self.template_path}")
                return self._create_minimal_config()
                
        except Exception as e:
            self.logger.error(f"❌ Erreur création depuis template: {e}")
            return self._create_minimal_config()
    
    def _create_minimal_config(self):
        """Configuration minimale par défaut"""
        return {
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 587,
                "username": "CONFIGURE_ME@gmail.com",
                "password": "CONFIGURE_APP_PASSWORD",
                "use_tls": True
            },
            "recipients": {
                "daily": ["admin@example.com"],
                "weekly": ["admin@example.com"]
            },
            "sender": {
                "name": "Trading Bot",
                "email": "CONFIGURE_ME@gmail.com"
            },
            "settings": {
                "send_daily": False,  # Désactivé par défaut
                "send_weekly": False,
                "attach_performance": True,
                "max_attachment_size_mb": 5
            }
        }
    
    def is_configured(self):
        """Vérifie si la configuration est complète"""
        try:
            smtp = self.config.get('smtp', {})
            
            # Vérifier les champs obligatoires
            required_fields = ['server', 'username', 'password']
            for field in required_fields:
                value = smtp.get(field, '')
                if not value or 'CONFIGURE' in str(value).upper():
                    return False, f"Champ '{field}' non configuré"
            
            # Vérifier les destinataires
            recipients = self.config.get('recipients', {})
            if not recipients.get('daily') and not recipients.get('weekly'):
                return False, "Aucun destinataire configuré"
            
            return True, "Configuration complète"
            
        except Exception as e:
            return False, f"Erreur validation: {e}"
    
    def send_daily_report(self):
        """Envoie le rapport quotidien"""
        try:
            # Vérifier la configuration
            is_valid, message = self.is_configured()
            if not is_valid:
                self.logger.error(f"❌ Configuration invalide: {message}")
                return False
            
            if not self.config['settings']['send_daily']:
                self.logger.info("📧 Envoi quotidien désactivé dans la configuration")
                return False
            
            self.logger.info("📧 Génération du rapport quotidien...")
            
            # Générer le rapport de monitoring
            os.system('./monitor.sh')
            
            # Lire le rapport
            report_path = "logs/daily_report.log"
            if not os.path.exists(report_path):
                self.logger.error(f"❌ Rapport quotidien non trouvé: {report_path}")
                return False
            
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # Statistiques rapides CORRIGÉES
            stats_info = self._get_quick_stats()
            
            # Préparer l'email
            today = datetime.now().strftime('%d/%m/%Y')
            subject = f"📊 Trading Bot - Rapport Quotidien {today}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; }}
                    .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .stat {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                    .report {{ background: #f4f4f4; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap; }}
                    .footer {{ color: #666; font-size: 12px; padding: 15px; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🤖 Enhanced Trading Bot - Rapport Quotidien</h2>
                        <p>📅 {today} • 🍓 Raspberry Pi Zero W2</p>
                    </div>
                    
                    <div class="content">
                        <div class="stats">
                            <div class="stat">
                                <strong>🔄 Exécutions</strong><br>
                                <span style="font-size: 24px; color: #28a745;">{stats_info.get('executions', 'N/A')}</span>
                            </div>
                            <div class="stat">
                                <strong>💰 Transactions</strong><br>
                                <span style="font-size: 24px; color: #007bff;">{stats_info.get('transactions', 'N/A')}</span>
                            </div>
                            <div class="stat">
                                <strong>🎯 OCO Actifs</strong><br>
                                <span style="font-size: 24px; color: #ffc107;">{stats_info.get('oco_active', 'N/A')}</span>
                            </div>
                        </div>
                        
                        <h3>📊 Rapport Détaillé:</h3>
                        <div class="report">{report_content}</div>
                    </div>
                    
                    <div class="footer">
                        📧 Email automatique du système Enhanced Trading Bot<br>
                        🔧 Configuration: {self.config_path}
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(
                recipients=self.config['recipients']['daily'],
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi rapport quotidien: {e}")
            return False
    
    def send_weekly_performance(self):
        """Envoie le rapport de performance hebdomadaire"""
        try:
            # Vérifications
            is_valid, message = self.is_configured()
            if not is_valid:
                self.logger.error(f"❌ Configuration invalide: {message}")
                return False
            
            if not self.config['settings']['send_weekly']:
                self.logger.info("📧 Envoi hebdomadaire désactivé dans la configuration")
                return False
            
            self.logger.info("📈 Génération du rapport performance hebdomadaire...")
            
            # Générer le rapport de performance
            performance_file = f"performance_weekly_{datetime.now().strftime('%Y%m%d')}.txt"
            os.system(f'python3 performance_stats.py --export {performance_file} --full --days 7')
            
            # Lire le rapport
            performance_content = "Rapport non généré"
            if os.path.exists(performance_file):
                with open(performance_file, 'r', encoding='utf-8') as f:
                    performance_content = f.read()
            
            # Statistiques de la semaine
            stats_info = self._get_weekly_stats()
            
            # Préparer l'email
            today = datetime.now().strftime('%d/%m/%Y')
            subject = f"📈 Trading Bot - Performance Hebdomadaire {today}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; }}
                    .performance {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                    .report {{ background: #f4f4f4; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 11px; overflow-x: auto; white-space: pre-wrap; max-height: 500px; overflow-y: auto; }}
                    .footer {{ color: #666; font-size: 12px; padding: 15px; border-top: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>📈 Enhanced Trading Bot - Performance Hebdomadaire</h2>
                        <p>📅 Semaine du {today} • 🍓 Raspberry Pi Zero W2</p>
                    </div>
                    
                    <div class="content">
                        <div class="performance">
                            <h3>💰 Résumé Performance (7 jours):</h3>
                            <p><strong>🔄 Transactions totales:</strong> {stats_info.get('total_transactions', 'N/A')}</p>
                            <p><strong>💵 Volume traité:</strong> {stats_info.get('volume', 'N/A')} USDC</p>
                            <p><strong>📈 Profit estimé:</strong> {stats_info.get('profit', 'Calcul en cours...')}</p>
                        </div>
                        
                        <h3>📊 Rapport Détaillé:</h3>
                        <div class="report">{performance_content}</div>
                    </div>
                    
                    <div class="footer">
                        📧 Email automatique hebdomadaire du système Enhanced Trading Bot<br>
                        🗓️ Prochain rapport: {(datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Préparer pièce jointe
            attachments = []
            if (self.config['settings']['attach_performance'] and 
                os.path.exists(performance_file) and 
                os.path.getsize(performance_file) < self.config['settings']['max_attachment_size_mb'] * 1024 * 1024):
                
                attachments.append({
                    'path': performance_file,
                    'name': f'trading_performance_{datetime.now().strftime("%Y%m%d")}.txt'
                })
            
            result = self._send_email(
                recipients=self.config['recipients']['weekly'],
                subject=subject,
                html_content=html_content,
                attachments=attachments
            )
            
            # Nettoyer
            if os.path.exists(performance_file):
                os.remove(performance_file)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi rapport hebdomadaire: {e}")
            return False
    
    def _get_quick_stats(self):
        """Récupère des statistiques rapides COHÉRENTES avec monitor.sh"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            executions = 0
            
            # MÉTHODE IDENTIQUE À monitor.sh
            if os.path.exists('logs/cron.log'):
                with open('logs/cron.log', 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Compter les débuts d'exécution (même logique que monitor.sh)
                    executions = content.count(f'{today}') 
                    lines_today = [line for line in content.split('\n') if today in line]
                    # Compter seulement les "=== DÉBUT EXECUTION CRON ===" 
                    executions = len([line for line in lines_today if "=== DÉBUT EXECUTION CRON ===" in line])
            
            # Stats depuis la DB si disponible
            try:
                import sqlite3
                conn = sqlite3.connect('db/trading.db')
                
                cursor = conn.execute("SELECT COUNT(*) FROM transactions WHERE date(created_at) = date('now')")
                transactions = cursor.fetchone()[0] or 0
                
                cursor = conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
                oco_active = cursor.fetchone()[0] or 0
                
                conn.close()
            except Exception as db_error:
                self.logger.debug(f"Erreur DB: {db_error}")
                transactions = 'N/A'
                oco_active = 'N/A'
            
            return {
                'executions': executions,
                'transactions': transactions,
                'oco_active': oco_active
            }
            
        except Exception as e:
            self.logger.debug(f"Erreur stats rapides: {e}")
            return {'executions': 'N/A', 'transactions': 'N/A', 'oco_active': 'N/A'}
    
    def _get_weekly_stats(self):
        """Statistiques hebdomadaires"""
        try:
            import sqlite3
            conn = sqlite3.connect('db/trading.db')
            
            # Transactions 7 derniers jours
            cursor = conn.execute("""
                SELECT COUNT(*), 
                       COALESCE(SUM(CASE WHEN order_side='BUY' THEN price*qty ELSE 0 END), 0) as volume,
                       COALESCE(SUM(CASE WHEN order_side='SELL' THEN price*qty ELSE -price*qty END), 0) as profit
                FROM transactions 
                WHERE created_at >= date('now', '-7 days')
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            return {
                'total_transactions': result[0] if result[0] else 0,
                'volume': f"{result[1]:.2f}" if result[1] else "0.00",
                'profit': f"{result[2]:+.2f}" if result[2] else "+0.00"
            }
        except Exception as e:
            self.logger.debug(f"Erreur stats hebdomadaires: {e}")
            return {'total_transactions': 'N/A', 'volume': 'N/A', 'profit': 'N/A'}
    
    def _send_email(self, recipients, subject, html_content, attachments=None):
        """Envoie un email avec gestion d'erreurs améliorée"""
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config['sender']['name']} <{self.config['sender']['email']}>"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Ajouter les pièces jointes
            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment['path']):
                        with open(attachment['path'], "rb") as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["name"]}'
                        )
                        msg.attach(part)
            
            # Connexion SMTP
            smtp_config = self.config['smtp']
            self.logger.info(f"📧 Connexion SMTP à {smtp_config['server']}:{smtp_config['port']}")
            
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            
            if smtp_config.get('use_tls', True):
                server.starttls()
            
            server.login(smtp_config['username'], smtp_config['password'])
            
            # Envoi
            text = msg.as_string()
            server.sendmail(self.config['sender']['email'], recipients, text)
            server.quit()
            
            self.logger.info(f"✅ Email envoyé avec succès à {len(recipients)} destinataire(s)")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"❌ Erreur authentification SMTP: {e}")
            self.logger.error("💡 Vérifiez username/password et activez les mots de passe d'application")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"❌ Erreur SMTP: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erreur envoi email: {e}")
            return False
    
    def test_email_config(self):
        """Test complet de la configuration email"""
        try:
            print("🧪 === TEST CONFIGURATION EMAIL ===")
            
            # Vérifier la config
            is_valid, message = self.is_configured()
            print(f"📋 Validation config: {message}")
            
            if not is_valid:
                print("❌ Configuration incomplète - éditez config/email_config.json")
                return False
            
            # Afficher la config (masquée)
            smtp = self.config['smtp']
            print(f"📧 Serveur SMTP: {smtp['server']}:{smtp['port']}")
            print(f"👤 Utilisateur: {smtp['username']}")
            print(f"🔒 Mot de passe: {'*' * len(smtp['password'])}")
            print(f"📮 Destinataires quotidiens: {len(self.config['recipients']['daily'])}")
            print(f"📮 Destinataires hebdomadaires: {len(self.config['recipients']['weekly'])}")
            
            # Test d'envoi
            test_content = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; border: 2px solid #28a745; border-radius: 10px; padding: 20px;">
                    <h2 style="color: #28a745; text-align: center;">🧪 Test Email Trading Bot</h2>
                    <p>Ce message confirme que la configuration email fonctionne correctement.</p>
                    <p><strong>⏰ Timestamp:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>🍓 Système:</strong> Raspberry Pi Zero W2</p>
                    <p><strong>📧 Serveur:</strong> {smtp['server']}</p>
                    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #155724; margin: 0; text-align: center;">
                            <strong>✅ Configuration email validée avec succès !</strong>
                        </p>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        Si vous recevez cet email, votre bot peut envoyer des rapports automatiques.
                    </p>
                </div>
            </body>
            </html>
            """
            
            print("\n📤 Envoi email de test...")
            result = self._send_email(
                recipients=self.config['recipients']['daily'][:1],  # Premier destinataire seulement
                subject=f"🧪 Test Email Trading Bot - {datetime.now().strftime('%d/%m %H:%M')}",
                html_content=test_content
            )
            
            if result:
                print("✅ Test email réussi ! Vérifiez votre boîte mail.")
                print("🎯 Vous pouvez maintenant activer les envois automatiques.")
            else:
                print("❌ Test email échoué ! Vérifiez les logs pour plus de détails.")
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur test email: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Système d'email Enhanced Trading Bot")
    parser.add_argument("--daily", action="store_true", help="Envoyer rapport quotidien")
    parser.add_argument("--weekly", action="store_true", help="Envoyer rapport hebdomadaire") 
    parser.add_argument("--test", action="store_true", help="Test de configuration email")
    parser.add_argument("--config", default="config/email_config.json", help="Chemin config email")
    
    args = parser.parse_args()
    
    mailer = TradingBotMailer(args.config)
    
    if args.test:
        mailer.test_email_config()
    elif args.daily:
        mailer.send_daily_report()
    elif args.weekly:
        mailer.send_weekly_performance()
    else:
        print("\n📧 === ENHANCED TRADING BOT - EMAIL SYSTEM ===")
        print("Usage:")
        print("  python3 email_sender.py --test      # Tester la configuration")
        print("  python3 email_sender.py --daily     # Rapport quotidien")
        print("  python3 email_sender.py --weekly    # Rapport hebdomadaire")
        print("\nPour configurer, éditez: config/email_config.json")

if __name__ == "__main__":
    main()
