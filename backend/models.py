# ============================================================
# FICHIER : backend/models.py
# RÔLE    : Définition des tables de la base de données
#
# CONCEPT POUR DÉBUTANT :
#   Chaque classe Python ici correspond à une table SQLite.
#   Chaque attribut de classe correspond à une colonne de la table.
#   SQLAlchemy traduit automatiquement ces classes en SQL.
#
#   Exemple :
#   class User(Base):           →  CREATE TABLE users (
#       id = Column(Integer)    →      id INTEGER,
#       email = Column(String)  →      email VARCHAR
#                               →  );
# ============================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# ============================================================
# TABLE : plants (Catalogue de plantes)
# ============================================================
class Plant(Base):
    """
    Catalogue de référence des plantes, notamment celles de Côte d'Ivoire.
    """
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    # Nom commun français (ex: "Manioc")

    local_name = Column(String(200), nullable=True)
    # Nom local ivoirien (dioula, baoulé, etc.)

    scientific_name = Column(String(200), nullable=False, unique=True, index=True)
    # Nom scientifique (ex: "Manihot esculenta")

    family = Column(String(100), nullable=True)
    # Famille botanique (ex: "Euphorbiaceae")

    description = Column(Text, nullable=True)
    # Description générale de la plante

    habitat = Column(String(200), nullable=True)
    # Milieu naturel (forêt, savane, zone côtière...)

    regions = Column(String(300), nullable=True)
    # Zones de Côte d'Ivoire où on la trouve

    is_edible = Column(Boolean, default=False)
    is_toxic = Column(Boolean, default=False)
    is_medicinal = Column(Boolean, default=False)
    is_invasive = Column(Boolean, default=False)

    toxicity_level = Column(String(20), default="aucun")
    # "aucun", "faible", "moyen", "élevé"

    culinary_uses = Column(Text, nullable=True)
    # Utilisations culinaires

    medicinal_uses = Column(Text, nullable=True)
    # Propriétés et usages médicinaux

    created_at = Column(DateTime, default=datetime.utcnow)




# ============================================================
# TABLE : users (Utilisateurs)
# ============================================================
class User(Base):
    """
    Représente un utilisateur de l'application.
    Contient les informations de connexion et de profil.
    """
    # Nom de la table dans SQLite
    __tablename__ = "users"

    # --- Colonnes ---
    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True  : identifiant unique, auto-incrémenté
    # index=True        : rend les recherches par id plus rapides

    username = Column(String(50), unique=True, nullable=False)
    # unique=True    : deux utilisateurs ne peuvent pas avoir le même nom
    # nullable=False : ce champ est obligatoire

    email = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String(200), nullable=True)
    # nullable=True : les comptes Google n'ont pas de mot de passe local
    # On ne stocke JAMAIS le mot de passe en clair !
    # On stocke uniquement son "hash" (version chiffrée)

    google_id = Column(String(100), nullable=True, unique=True, index=True)
    # Identifiant unique Google (sub) — rempli lors d'une connexion Google

    created_at = Column(DateTime, default=datetime.utcnow)
    # default=datetime.utcnow : la date est automatiquement remplie
    # lors de la création d'un utilisateur

    # --- Vérification de compte ---
    is_verified = Column(Boolean, default=False)
    # False = compte créé mais email non confirmé
    # True  = l'utilisateur a cliqué sur le lien de vérification

    verification_token = Column(String(100), nullable=True)
    # Token UUID envoyé par email à l'inscription
    # Mis à None après vérification réussie

    verification_token_expires = Column(DateTime, nullable=True)
    # Date d'expiration du token de vérification (24h après création)

    # --- Réinitialisation du mot de passe ---
    reset_token = Column(String(100), nullable=True)
    # Token UUID envoyé par email lors d'une demande de réinitialisation

    reset_token_expires = Column(DateTime, nullable=True)
    # Date d'expiration du token de réinitialisation (1 heure après création)

    token_version = Column(Integer, default=0, nullable=False)
    # Incrémenté à chaque changement de mot de passe pour invalider les anciens JWT

    # --- Relations (liens avec d'autres tables) ---
    # Un utilisateur peut avoir plusieurs scans
    scans = relationship("Scan", back_populates="user")
    # back_populates="user" : depuis un scan, on peut accéder à scan.user


# ============================================================
# TABLE : scans (Analyses de plantes)
# ============================================================
class Scan(Base):
    """
    Représente une analyse de plante.
    Contient l'image, les résultats d'identification et le rapport complet.
    """
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)

    # Clé étrangère : lie ce scan à un utilisateur
    # ForeignKey("users.id") signifie : cette valeur doit exister dans users.id
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # --- Informations sur l'image ---
    image_path = Column(String(300), nullable=False)
    # Chemin relatif vers l'image stockée (ex: "uploads/abc123.jpg")

    # --- Résultats de PlantNet ---
    plant_name = Column(String(200))
    # Nom commun de la plante (ex: "Tomate")

    plant_scientific_name = Column(String(200))
    # Nom scientifique (ex: "Solanum lycopersicum")

    plant_family = Column(String(100))
    # Famille botanique (ex: "Solanaceae")

    confidence_score = Column(Float)
    # Score de confiance de l'identification (0.0 à 1.0)
    # Ex: 0.95 = 95% de certitude

    # --- Rapport IA (stocké en JSON sous forme de texte) ---
    report_json = Column(Text)
    # Le rapport complet généré par Groq, au format JSON
    # On utilise Text car JSON peut être très long

    # --- Localisation (optionnelle) ---
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # Coordonnées GPS si l'utilisateur a autorisé la géolocalisation

    # --- Métadonnées extraites du rapport (pour les filtres et analytics) ---
    is_edible = Column(Boolean, default=False)
    # La plante est-elle comestible ?

    is_toxic = Column(Boolean, default=False)
    # La plante est-elle toxique ?

    is_medicinal = Column(Boolean, default=False)
    # La plante a-t-elle des propriétés médicinales ?

    is_invasive = Column(Boolean, default=False)
    # La plante est-elle invasive/nuisible pour l'environnement ?

    toxicity_level = Column(String(20), default="aucun")
    # Niveau de toxicité : "aucun", "faible", "moyen", "élevé"

    # --- Correspondance avec le catalogue local ---
    local_plant_id   = Column(Integer, ForeignKey("plants.id"), nullable=True)
    # ID de la plante trouvée dans notre catalogue local (si correspondance)

    local_plant_name = Column(String(200), nullable=True)
    # Nom local conservé en clair pour éviter une jointure à chaque lecture

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    deleted_at = Column(DateTime, nullable=True, default=None)
    # NULL = actif  |  datetime = supprimé (soft-delete, conservation pour audit)

    # --- Relations ---
    user = relationship("User", back_populates="scans")
    # Depuis un scan, on peut accéder à scan.user pour voir l'utilisateur

    messages = relationship("ChatMessage", back_populates="scan", cascade="all, delete-orphan")
    # Un scan peut avoir plusieurs messages de chat
    # cascade="all, delete-orphan" : si on supprime un scan,
    # tous ses messages sont automatiquement supprimés aussi


# ============================================================
# TABLE : chat_messages (Messages du chat IA)
# ============================================================
class ChatMessage(Base):
    """
    Représente un message dans la conversation avec l'agent IA.
    Chaque message est lié à un scan spécifique.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Lien vers le scan associé
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)

    role = Column(String(20), nullable=False)
    # Qui a envoyé le message ?
    # "user"      : message de l'utilisateur
    # "assistant" : réponse de l'IA

    content = Column(Text, nullable=False)
    # Contenu du message (peut être très long)

    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relations ---
    scan = relationship("Scan", back_populates="messages")
