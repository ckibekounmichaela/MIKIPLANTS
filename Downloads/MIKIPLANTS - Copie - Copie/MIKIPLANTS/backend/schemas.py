# ============================================================
# FICHIER : backend/schemas.py
# RÔLE    : Définition des structures de données (validation)
#
# CONCEPT POUR DÉBUTANT :
#   Pydantic est une bibliothèque de validation de données.
#   Les "schemas" définissent la forme exacte des données
#   que l'API accepte (entrée) et renvoie (sortie).
#
#   Différence avec les models.py :
#   - models.py  → structure des TABLES en base de données
#   - schemas.py → structure des DONNÉES échangées via l'API
#     (ce que le client envoie et ce que l'API répond)
# ============================================================

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ============================================================
# SCHEMAS D'AUTHENTIFICATION
# ============================================================

class UserCreate(BaseModel):
    """
    Données nécessaires pour créer un nouveau compte.
    Le client doit envoyer exactement ces champs.
    """
    username: str       # Ex: "jean_dupont"
    email: EmailStr     # EmailStr valide automatiquement le format email
    password: str       # Mot de passe en clair (sera hashé côté serveur)


class ForgotPasswordRequest(BaseModel):
    """Données pour demander la réinitialisation du mot de passe."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Données pour choisir un nouveau mot de passe."""
    token: str          # Token reçu par email
    new_password: str   # Nouveau mot de passe (minimum 6 caractères)


class ChangePasswordRequest(BaseModel):
    """Données pour changer le mot de passe depuis le profil (utilisateur connecté)."""
    current_password: str   # Mot de passe actuel (pour vérification)
    new_password: str       # Nouveau mot de passe (minimum 6 caractères)


class UserLogin(BaseModel):
    """
    Données pour se connecter.
    """
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Ce que l'API renvoie quand elle parle d'un utilisateur.
    On n'inclut PAS le mot de passe dans la réponse !
    """
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        # orm_mode=True permet à Pydantic de lire les données
        # directement depuis un objet SQLAlchemy (pas seulement des dicts)
        from_attributes = True


class Token(BaseModel):
    """
    Réponse renvoyée après une connexion réussie.
    """
    access_token: str   # Le token JWT que le client devra garder
    token_type: str     # Toujours "bearer" (standard HTTP)


# ============================================================
# SCHEMAS DE SCAN
# ============================================================

class PlantNetResult(BaseModel):
    """
    Résultat brut de l'API PlantNet après identification.
    """
    plant_name: str             # Nom commun
    scientific_name: str        # Nom scientifique
    family: str                 # Famille botanique
    confidence_score: float     # Score entre 0 et 1


class HealthReport(BaseModel):
    """Rapport sur la santé de la plante."""
    status: str                 # "Bonne santé" ou "Maladie détectée"
    diseases: List[str]         # Liste des maladies détectées
    treatments: List[str]       # Traitements recommandés


class EdibilityReport(BaseModel):
    """Rapport sur la comestibilité."""
    verdict: str                # "oui", "non", ou "partiel"
    edible_parts: List[str]     # Parties comestibles (feuilles, fruits...)
    recipes: List[str]          # Idées de recettes simples
    warnings: List[str]         # Précautions à prendre


class MedicinalReport(BaseModel):
    """Rapport sur les propriétés médicinales."""
    uses: List[str]             # Usages traditionnels documentés
    dosage: str                 # Posologie de base
    contraindications: List[str] # Contre-indications


class ToxicityReport(BaseModel):
    """Rapport sur la toxicité."""
    level: str                  # "aucun", "faible", "moyen", "élevé"
    symptoms: List[str]         # Symptômes possibles en cas d'ingestion
    first_aid: str              # Premiers secours


class EnvironmentReport(BaseModel):
    """Rapport sur l'impact environnemental."""
    invasive: bool              # Espèce invasive ?
    allelopathic: bool          # Nuit aux autres plantes ?
    soil_impact: str            # Impact sur le sol
    agricultural_impact: str    # Impact sur les cultures


class PlantReport(BaseModel):
    """
    Rapport complet généré par l'IA.
    Contient les 5 sections d'analyse.
    """
    health: HealthReport
    edibility: EdibilityReport
    medicinal: MedicinalReport
    toxicity: ToxicityReport
    environment: EnvironmentReport


class LocalPlantMatch(BaseModel):
    """Données de correspondance avec notre catalogue local CI."""
    id: int
    name: str
    local_name: Optional[str]
    scientific_name: str
    habitat: Optional[str]
    regions: Optional[str]
    culinary_uses: Optional[str]
    medicinal_uses: Optional[str]

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """
    Réponse complète après l'analyse d'une plante.
    Envoyée au client après un scan réussi.
    """
    id: int
    plant_name: str
    plant_scientific_name: str
    plant_family: str
    confidence_score: float
    image_path: str
    report: Optional[dict]      # Le rapport JSON complet
    is_edible: bool
    is_toxic: bool
    is_medicinal: bool
    is_invasive: bool
    toxicity_level: str
    local_match: Optional[LocalPlantMatch] = None
    # Données locales CI trouvées dans notre catalogue (None si non trouvé)
    created_at: datetime

    class Config:
        from_attributes = True


class ScanListItem(BaseModel):
    """
    Version résumée d'un scan pour la liste de l'historique.
    Moins de données que ScanResponse pour ne pas surcharger.
    """
    id: int
    plant_name: str
    plant_scientific_name: str
    confidence_score: float
    image_path: str
    is_edible: bool
    is_toxic: bool
    is_medicinal: bool
    is_invasive: bool
    toxicity_level: str
    latitude: Optional[float] = None    # GPS (si autorisé)
    longitude: Optional[float] = None   # GPS (si autorisé)
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# SCHEMAS DE CHAT
# ============================================================

class ChatMessageCreate(BaseModel):
    """Données envoyées par l'utilisateur pour poser une question."""
    message: str    # La question de l'utilisateur


class ChatMessageResponse(BaseModel):
    """Un message du chat (utilisateur ou assistant)."""
    id: int
    role: str       # "user" ou "assistant"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Réponse de l'agent IA."""
    response: str               # La réponse de l'IA
    message_id: int             # ID du message sauvegardé


# ============================================================
# SCHEMAS D'ANALYTICS
# ============================================================

class AnalyticsSummary(BaseModel):
    """Statistiques globales pour le tableau de bord."""
    total_scans: int            # Nombre total d'analyses
    total_users: int            # Nombre d'utilisateurs
    unique_plants: int          # Nombre de plantes uniques identifiées
    toxic_plants_count: int     # Nombre de plantes toxiques trouvées
    edible_plants_count: int    # Nombre de plantes comestibles
    medicinal_plants_count: int # Nombre de plantes médicinales
    invasive_plants_count: int  # Nombre de plantes invasives


class TopPlant(BaseModel):
    """Une plante avec son nombre de scans (pour le classement)."""
    plant_name: str
    scientific_name: str
    scan_count: int


class TimelinePoint(BaseModel):
    """Point de données pour le graphique d'évolution dans le temps."""
    date: str       # Format "YYYY-MM-DD"
    count: int      # Nombre de scans ce jour-là


# ============================================================
# SCHEMAS DU CATALOGUE DE PLANTES
# ============================================================

class PlantResponse(BaseModel):
    """Réponse complète pour une plante du catalogue."""
    id: int
    name: str
    local_name: Optional[str]
    scientific_name: str
    family: Optional[str]
    description: Optional[str]
    habitat: Optional[str]
    regions: Optional[str]
    is_edible: bool
    is_toxic: bool
    is_medicinal: bool
    is_invasive: bool
    toxicity_level: str
    culinary_uses: Optional[str]
    medicinal_uses: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PlantListItem(BaseModel):
    """Version résumée d'une plante pour les listes."""
    id: int
    name: str
    local_name: Optional[str]
    scientific_name: str
    family: Optional[str]
    is_edible: bool
    is_toxic: bool
    is_medicinal: bool
    is_invasive: bool
    toxicity_level: str

    class Config:
        from_attributes = True


class PlantCatalogStats(BaseModel):
    """Statistiques du catalogue de plantes."""
    total: int
    edible: int
    medicinal: int
    toxic: int
    invasive: int
