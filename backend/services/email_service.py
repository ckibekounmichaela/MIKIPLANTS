# ============================================================
# FICHIER : backend/services/email_service.py
# RÔLE    : Envoi d'emails transactionnels via SMTP
#
# FONCTIONNALITÉS :
#   1. Email de vérification du compte à l'inscription
#   2. Email de notification de connexion
#   3. Email de réinitialisation du mot de passe
#
# CONFIGURATION REQUISE dans .env :
#   SMTP_HOST     : ex. smtp.gmail.com
#   SMTP_PORT     : ex. 587 (TLS) ou 465 (SSL)
#   SMTP_USER     : votre adresse email (ex. monapp@gmail.com)
#   SMTP_PASSWORD : mot de passe ou "App Password" Google
#   APP_BASE_URL  : ex. http://localhost:8000
#
# POUR GMAIL :
#   Activez "Accès aux applications moins sécurisées" OU
#   créez un "Mot de passe d'application" (recommandé) :
#   Compte Google → Sécurité → Validation en 2 étapes → Mots de passe d'application
# ============================================================

import html as _html
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Charger la configuration SMTP depuis les variables d'environnement
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
APP_BASE_URL  = os.getenv("APP_BASE_URL", "http://localhost:8000")
FROM_NAME     = "MikiPlants"


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Fonction interne : envoie un email HTML via SMTP.

    PARAMÈTRES :
        to_email  : Adresse email du destinataire
        subject   : Sujet de l'email
        html_body : Corps de l'email en HTML

    RETOUR :
        True si l'envoi a réussi, False sinon.

    FONCTIONNEMENT SMTP :
        1. On crée le message (headers + corps HTML)
        2. On se connecte au serveur SMTP
        3. On s'authentifie avec nos identifiants
        4. On envoie le message
        5. On ferme la connexion
    """
    # Vérifier que les identifiants SMTP sont configurés
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL] AVERTISSEMENT: SMTP non configuré. Email NON envoyé à {to_email}")
        print(f"[EMAIL] Sujet: {subject}")
        return False

    try:
        # Créer le message email (format MIME multipart)
        # MIMEMultipart("alternative") = message avec plusieurs versions (texte + HTML)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
        msg["To"]      = to_email

        # Ajouter le corps HTML
        # MIMEText avec "html" = le navigateur email affichera le HTML
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        # Se connecter au serveur SMTP avec STARTTLS (port 587)
        # STARTTLS = commence en texte clair puis passe en chiffré
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()           # Identifier notre client au serveur
            server.starttls()       # Activer le chiffrement TLS
            server.ehlo()           # Re-identifier après TLS
            server.login(SMTP_USER, SMTP_PASSWORD)  # S'authentifier
            server.sendmail(SMTP_USER, to_email, msg.as_string())  # Envoyer

        print(f"[EMAIL] Email envoyé avec succès à {to_email} : {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(f"[EMAIL] ERREUR: Authentification SMTP échouée. Vérifiez SMTP_USER et SMTP_PASSWORD dans .env")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] ERREUR SMTP: {str(e)}")
        return False
    except Exception as e:
        print(f"[EMAIL] ERREUR inattendue: {str(e)}")
        return False


# ============================================================
# EMAIL 1 : VÉRIFICATION DU COMPTE (à l'inscription)
# ============================================================

def send_verification_email(to_email: str, username: str, token: str) -> bool:
    """
    Envoyer l'email de vérification du compte après inscription.

    L'utilisateur doit cliquer sur le lien pour activer son compte.

    PARAMÈTRES :
        to_email : Email du nouvel utilisateur
        username : Nom d'utilisateur
        token    : Token de vérification unique (UUID)
    """
    safe_username = _html.escape(username)
    verify_url = f"{APP_BASE_URL}/verify-email?token={token}"

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; margin:0; padding:20px;">
      <div style="max-width:600px; margin:0 auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.1);">

        <!-- En-tête vert -->
        <div style="background:#198754; padding:30px; text-align:center;">
          <h1 style="color:white; margin:0; font-size:28px;">🌿 MikiPlants</h1>
          <p style="color:#d4edda; margin:8px 0 0;">Identification intelligente de plantes</p>
        </div>

        <!-- Corps -->
        <div style="padding:30px;">
          <h2 style="color:#333;">Bienvenue, {safe_username} !</h2>
          <p style="color:#555; line-height:1.6;">
            Merci de vous être inscrit sur <strong>MikiPlants</strong>.
            Pour activer votre compte et commencer à analyser des plantes,
            veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous.
          </p>

          <!-- Bouton de vérification -->
          <div style="text-align:center; margin:30px 0;">
            <a href="{verify_url}"
               style="background:#198754; color:white; padding:14px 32px; border-radius:8px;
                      text-decoration:none; font-size:16px; font-weight:bold; display:inline-block;">
              ✅ Vérifier mon adresse email
            </a>
          </div>

          <p style="color:#777; font-size:13px;">
            Ce lien est valable pendant <strong>24 heures</strong>.<br>
            Si vous n'avez pas créé de compte, ignorez cet email.
          </p>

          <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
          <p style="color:#999; font-size:12px;">
            Lien direct si le bouton ne fonctionne pas :<br>
            <a href="{verify_url}" style="color:#198754;">{verify_url}</a>
          </p>
        </div>

        <!-- Pied de page -->
        <div style="background:#f8f9fa; padding:15px; text-align:center;">
          <p style="color:#999; font-size:12px; margin:0;">
            © {datetime.now().year} MikiPlants – Application d'analyse de plantes
          </p>
        </div>

      </div>
    </body>
    </html>
    """

    return _send_email(to_email, "✅ Vérifiez votre adresse email – MikiPlants", html)


# ============================================================
# EMAIL 2 : NOTIFICATION DE CONNEXION
# ============================================================

def send_login_notification(to_email: str, username: str, ip_address: str = "Inconnue") -> bool:
    """
    Notifier l'utilisateur qu'une connexion a eu lieu sur son compte.

    Utile pour détecter les connexions non autorisées.

    PARAMÈTRES :
        to_email   : Email de l'utilisateur
        username   : Nom d'utilisateur
        ip_address : Adresse IP du client (pour information)
    """
    safe_username = _html.escape(username)
    safe_ip       = _html.escape(ip_address)
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; margin:0; padding:20px;">
      <div style="max-width:600px; margin:0 auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.1);">

        <!-- En-tête -->
        <div style="background:#198754; padding:30px; text-align:center;">
          <h1 style="color:white; margin:0; font-size:28px;">🌿 MikiPlants</h1>
        </div>

        <!-- Corps -->
        <div style="padding:30px;">
          <h2 style="color:#333;">Nouvelle connexion détectée</h2>
          <p style="color:#555; line-height:1.6;">
            Bonjour <strong>{safe_username}</strong>,<br><br>
            Une connexion a été effectuée sur votre compte MikiPlants.
          </p>

          <!-- Détails de connexion -->
          <div style="background:#f8f9fa; border-left:4px solid #198754; padding:15px; border-radius:4px; margin:20px 0;">
            <p style="margin:0; color:#555;">
              📅 <strong>Date :</strong> {now}<br>
              🌍 <strong>Adresse IP :</strong> {safe_ip}<br>
              👤 <strong>Compte :</strong> {to_email}
            </p>
          </div>

          <p style="color:#555; line-height:1.6;">
            Si vous êtes bien à l'origine de cette connexion, vous pouvez ignorer cet email.
          </p>

          <!-- Bouton si connexion suspecte -->
          <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:15px; margin:20px 0;">
            <p style="color:#856404; margin:0 0 10px; font-weight:bold;">
              ⚠️ Ce n'était pas vous ?
            </p>
            <p style="color:#856404; margin:0 0 15px; font-size:14px;">
              Changez immédiatement votre mot de passe pour sécuriser votre compte.
            </p>
            <a href="{APP_BASE_URL}/"
               style="background:#dc3545; color:white; padding:10px 20px; border-radius:6px;
                      text-decoration:none; font-size:14px; display:inline-block;">
              🔒 Sécuriser mon compte
            </a>
          </div>
        </div>

        <!-- Pied de page -->
        <div style="background:#f8f9fa; padding:15px; text-align:center;">
          <p style="color:#999; font-size:12px; margin:0;">
            © {datetime.now().year} MikiPlants – Cet email est envoyé automatiquement, ne pas y répondre.
          </p>
        </div>

      </div>
    </body>
    </html>
    """

    return _send_email(to_email, "🔐 Nouvelle connexion sur votre compte MikiPlants", html)


# ============================================================
# EMAIL 3 : RÉINITIALISATION DU MOT DE PASSE
# ============================================================

def send_password_reset_email(to_email: str, username: str, token: str) -> bool:
    """
    Envoyer le lien de réinitialisation du mot de passe.

    PARAMÈTRES :
        to_email : Email de l'utilisateur
        username : Nom d'utilisateur
        token    : Token de réinitialisation unique (UUID, valide 1 heure)
    """
    safe_username = _html.escape(username)
    reset_url = f"{APP_BASE_URL}/reset-password?token={token}"

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; margin:0; padding:20px;">
      <div style="max-width:600px; margin:0 auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.1);">

        <!-- En-tête -->
        <div style="background:#dc3545; padding:30px; text-align:center;">
          <h1 style="color:white; margin:0; font-size:28px;">🌿 MikiPlants</h1>
          <p style="color:#f8d7da; margin:8px 0 0;">Réinitialisation de mot de passe</p>
        </div>

        <!-- Corps -->
        <div style="padding:30px;">
          <h2 style="color:#333;">Mot de passe oublié ?</h2>
          <p style="color:#555; line-height:1.6;">
            Bonjour <strong>{safe_username}</strong>,<br><br>
            Vous avez demandé la réinitialisation de votre mot de passe.
            Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
          </p>

          <!-- Bouton de réinitialisation -->
          <div style="text-align:center; margin:30px 0;">
            <a href="{reset_url}"
               style="background:#dc3545; color:white; padding:14px 32px; border-radius:8px;
                      text-decoration:none; font-size:16px; font-weight:bold; display:inline-block;">
              🔑 Réinitialiser mon mot de passe
            </a>
          </div>

          <div style="background:#f8d7da; border:1px solid #f5c2c7; border-radius:8px; padding:15px; margin:20px 0;">
            <p style="color:#842029; margin:0; font-size:14px;">
              ⏰ <strong>Ce lien expire dans 1 heure.</strong><br>
              Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
              Votre mot de passe reste inchangé.
            </p>
          </div>

          <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
          <p style="color:#999; font-size:12px;">
            Lien direct si le bouton ne fonctionne pas :<br>
            <a href="{reset_url}" style="color:#dc3545;">{reset_url}</a>
          </p>
        </div>

        <!-- Pied de page -->
        <div style="background:#f8f9fa; padding:15px; text-align:center;">
          <p style="color:#999; font-size:12px; margin:0;">
            © {datetime.now().year} MikiPlants – Cet email est envoyé automatiquement.
          </p>
        </div>

      </div>
    </body>
    </html>
    """

    return _send_email(to_email, "🔑 Réinitialisation de votre mot de passe – MikiPlants", html)
