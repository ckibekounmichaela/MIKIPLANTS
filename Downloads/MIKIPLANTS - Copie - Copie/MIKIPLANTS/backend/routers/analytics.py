# ============================================================
# FICHIER : backend/routers/analytics.py
# RÔLE    : Endpoints pour les statistiques et le tableau de bord
#
# CONCEPT POUR DÉBUTANT :
#   Ces endpoints agrègent (regroupent) les données de la BD
#   pour produire des statistiques.
#   Ex: "combien de plantes toxiques ont été scannées ce mois ?"
#   On utilise les fonctions SQL de SQLAlchemy : count(), func...
# ============================================================

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from database import get_db
from models import Scan, User
from schemas import AnalyticsSummary, TopPlant, TimelinePoint
from routers.auth import get_current_user

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les statistiques globales pour le tableau de bord.
    Retourne des comptages agrégés de tous les scans.
    """

    # Compter le nombre total de scans de l'utilisateur
    total_scans = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id
    ).scalar()
    # scalar() retourne un seul nombre (pas une liste)

    # Compter les plantes uniques (par nom scientifique)
    unique_plants = db.query(func.count(func.distinct(Scan.plant_scientific_name))).filter(
        Scan.user_id == current_user.id
    ).scalar()

    # Compter les plantes toxiques
    toxic_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_toxic == True
    ).scalar()

    # Compter les plantes comestibles
    edible_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_edible == True
    ).scalar()

    # Compter les plantes médicinales
    medicinal_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_medicinal == True
    ).scalar()

    # Compter les plantes invasives
    invasive_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_invasive == True
    ).scalar()

    # Compter le nombre total d'utilisateurs (pour l'admin)
    total_users = db.query(func.count(User.id)).scalar()

    return AnalyticsSummary(
        total_scans=total_scans or 0,
        total_users=total_users or 0,
        unique_plants=unique_plants or 0,
        toxic_plants_count=toxic_count or 0,
        edible_plants_count=edible_count or 0,
        medicinal_plants_count=medicinal_count or 0,
        invasive_plants_count=invasive_count or 0
    )


@router.get("/top-plants", response_model=List[TopPlant])
def get_top_plants(
    limit: int = 10,    # Retourner les 10 plantes les plus scannées
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer le classement des plantes les plus scannées.
    """

    # Requête SQL équivalente :
    # SELECT plant_name, plant_scientific_name, COUNT(*) as scan_count
    # FROM scans
    # WHERE user_id = {current_user.id}
    # GROUP BY plant_name, plant_scientific_name
    # ORDER BY scan_count DESC
    # LIMIT {limit}

    results = db.query(
        Scan.plant_name,
        Scan.plant_scientific_name,
        func.count(Scan.id).label("scan_count")
    ).filter(
        Scan.user_id == current_user.id
    ).group_by(
        Scan.plant_name,
        Scan.plant_scientific_name
    ).order_by(
        desc("scan_count")
    ).limit(limit).all()

    # Convertir les résultats en liste de dictionnaires
    return [
        TopPlant(
            plant_name=row.plant_name or "Inconnue",
            scientific_name=row.plant_scientific_name or "",
            scan_count=row.scan_count
        )
        for row in results
    ]


@router.get("/distribution")
def get_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer la répartition comestible / toxique / médicinal.
    Données pour le graphique en camembert (donut chart).
    """
    total = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id
    ).scalar() or 1  # Éviter la division par zéro

    edible = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id, Scan.is_edible == True
    ).scalar() or 0

    toxic = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id, Scan.is_toxic == True
    ).scalar() or 0

    medicinal = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id, Scan.is_medicinal == True
    ).scalar() or 0

    invasive = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id, Scan.is_invasive == True
    ).scalar() or 0

    return {
        "labels": ["Comestibles", "Toxiques", "Médicinales", "Invasives"],
        "values": [edible, toxic, medicinal, invasive],
        "total": total
    }


@router.get("/timeline", response_model=List[TimelinePoint])
def get_timeline(
    days: int = 30,   # Données des 30 derniers jours par défaut
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'évolution du nombre de scans sur les derniers jours.
    Données pour le graphique en courbes.
    """
    # Date de début (il y a {days} jours)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Récupérer les scans récents
    scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.created_at >= start_date
    ).order_by(Scan.created_at.asc()).all()

    # Regrouper par jour
    # On crée un dictionnaire : {"2024-01-15": 3, "2024-01-16": 1, ...}
    daily_counts = {}
    for scan in scans:
        day_key = scan.created_at.strftime("%Y-%m-%d")
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    # Créer un point pour chaque jour (même les jours sans scan = 0)
    timeline = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        timeline.append(TimelinePoint(
            date=date,
            count=daily_counts.get(date, 0)
        ))

    return timeline


@router.get("/alerts")
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les alertes : plantes invasives et toxiques détectées récemment.
    """
    # Scans des 7 derniers jours avec plantes invasives ou très toxiques
    recent_alerts = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.created_at >= datetime.utcnow() - timedelta(days=7),
        (Scan.is_invasive == True) | (Scan.toxicity_level == "élevé")
    ).order_by(Scan.created_at.desc()).limit(10).all()

    alerts = []
    for scan in recent_alerts:
        alert_type = []
        if scan.is_invasive:
            alert_type.append("Espèce invasive")
        if scan.toxicity_level == "élevé":
            alert_type.append("Toxicité élevée")

        alerts.append({
            "scan_id": scan.id,
            "plant_name": scan.plant_name,
            "scientific_name": scan.plant_scientific_name,
            "alert_types": alert_type,
            "date": scan.created_at.strftime("%d/%m/%Y")
        })

    return {"alerts": alerts, "count": len(alerts)}


@router.get("/locations")
def get_scan_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer les coordonnées GPS de tous les scans avec localisation.
    Utilisé pour afficher la carte des scans.
    """
    scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.latitude  != None,
        Scan.longitude != None
    ).order_by(Scan.created_at.desc()).all()

    points = []
    for scan in scans:
        points.append({
            "id":           scan.id,
            "lat":          scan.latitude,
            "lng":          scan.longitude,
            "plant_name":   scan.plant_name or "Inconnue",
            "scientific":   scan.plant_scientific_name or "",
            "is_toxic":     scan.is_toxic,
            "is_invasive":  scan.is_invasive,
            "is_edible":    scan.is_edible,
            "is_medicinal": scan.is_medicinal,
            "date":         scan.created_at.strftime("%d/%m/%Y"),
            "image_path":   scan.image_path or ""
        })

    return {"points": points, "total": len(points)}
