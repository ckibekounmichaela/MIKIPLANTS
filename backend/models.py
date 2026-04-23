from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Plant(Base):
    """
    Catalogue de référence des plantes, notamment celles de Côte d'Ivoire.
    """
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)

    local_name = Column(String(200), nullable=True)

    scientific_name = Column(String(200), nullable=False, unique=True, index=True)

    family = Column(String(100), nullable=True)

    description = Column(Text, nullable=True)

    habitat = Column(String(200), nullable=True)

    regions = Column(String(300), nullable=True)

    is_edible = Column(Boolean, default=False)
    is_toxic = Column(Boolean, default=False)
    is_medicinal = Column(Boolean, default=False)
    is_invasive = Column(Boolean, default=False)

    toxicity_level = Column(String(20), default="aucun")

    culinary_uses = Column(Text, nullable=True)

    medicinal_uses = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    """
    Représente un utilisateur de l'application.
    Contient les informations de connexion et de profil.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)


    username = Column(String(50), unique=True, nullable=False)
   

    email = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String(200), nullable=True)
    

    google_id = Column(String(100), nullable=True, unique=True, index=True)
    # Identifiant unique Google (sub) — rempli lors d'une connexion Google

    created_at = Column(DateTime, default=datetime.utcnow)
   

    is_verified = Column(Boolean, default=False)
  

    verification_token = Column(String(100), nullable=True)
   

    verification_token_expires = Column(DateTime, nullable=True)

    
    reset_token = Column(String(100), nullable=True)

    reset_token_expires = Column(DateTime, nullable=True)

    token_version = Column(Integer, default=0, nullable=False)


    scans = relationship("Scan", back_populates="user")

class Scan(Base):
    """
    Représente une analyse de plante.
    Contient l'image, les résultats d'identification et le rapport complet.
    """
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)

    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    image_path = Column(String(300), nullable=False)

    plant_name = Column(String(200))

    plant_scientific_name = Column(String(200))

    plant_family = Column(String(100))

    confidence_score = Column(Float)
    

    report_json = Column(Text)
   

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    is_edible = Column(Boolean, default=False)

    is_toxic = Column(Boolean, default=False)

    is_medicinal = Column(Boolean, default=False)

    is_invasive = Column(Boolean, default=False)

    toxicity_level = Column(String(20), default="aucun")

    local_plant_id   = Column(Integer, ForeignKey("plants.id"), nullable=True)

    local_plant_name = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    deleted_at = Column(DateTime, nullable=True, default=None)

    user = relationship("User", back_populates="scans")

    messages = relationship("ChatMessage", back_populates="scan", cascade="all, delete-orphan")


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
    

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="messages")
