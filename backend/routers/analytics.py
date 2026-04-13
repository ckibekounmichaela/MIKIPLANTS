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

import json
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


@router.get("/diseases")
def get_diseases(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extraire et classer les maladies les plus fréquentes
    depuis le champ report_json de chaque scan.
    Le rapport IA stocke les maladies dans health.diseases (liste de strings).
    """
    scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.report_json != None
    ).all()

    disease_counts = {}
    for scan in scans:
        try:
            report = json.loads(scan.report_json)
            diseases = report.get("health", {}).get("diseases", [])
            for disease in diseases:
                # Ignorer les valeurs vides ou "aucune maladie"
                clean = disease.strip()
                if clean and clean.lower() not in ["aucune", "aucun", "none", "aucune maladie", "-"]:
                    disease_counts[clean] = disease_counts.get(clean, 0) + 1
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue

    # Trier par fréquence décroissante et limiter
    sorted_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {"disease": name, "count": count}
        for name, count in sorted_diseases
    ]


@router.get("/alerts")
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alertes en deux catégories :
      1. Alertes ponctuelles  : scans récents (7j) avec plantes invasives ou toxicité élevée
      2. Alertes de tendance  : augmentation soudaine cette semaine vs semaine précédente
                                (invasives, toxiques, maladies)
    """
    now = datetime.utcnow()
    week_start      = now - timedelta(days=7)
    prev_week_start = now - timedelta(days=14)

    # ---- 1. Alertes ponctuelles (scans individuels) ----
    recent_scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.created_at >= week_start,
        (Scan.is_invasive == True) | (Scan.toxicity_level == "élevé")
    ).order_by(Scan.created_at.desc()).limit(10).all()

    alerts = []
    for scan in recent_scans:
        alert_type = []
        if scan.is_invasive:
            alert_type.append("Espèce invasive")
        if scan.toxicity_level == "élevé":
            alert_type.append("Toxicité élevée")

        alerts.append({
            "type":            "scan",
            "scan_id":         scan.id,
            "plant_name":      scan.plant_name or "Inconnue",
            "scientific_name": scan.plant_scientific_name or "",
            "alert_types":     alert_type,
            "date":            scan.created_at.strftime("%d/%m/%Y")
        })

    # ---- 2. Alertes de tendance (semaine N vs semaine N-1) ----
    def count_week(filter_col, start, end):
        return db.query(func.count(Scan.id)).filter(
            Scan.user_id == current_user.id,
            Scan.created_at >= start,
            Scan.created_at <  end,
            filter_col == True
        ).scalar() or 0

    trend_checks = [
        ("invasive",  Scan.is_invasive, "Plantes invasives",  "warning"),
        ("toxic",     Scan.is_toxic,    "Plantes toxiques",   "danger"),
        ("medicinal", Scan.is_medicinal,"Plantes médicinales","info"),
    ]
    trend_alerts = []
    for key, col, label, severity in trend_checks:
        curr = count_week(col, week_start,      now)
        prev = count_week(col, prev_week_start, week_start)

        # Hausse significative : +50% ET au moins 2 scans supplémentaires
        if curr >= 2 and (prev == 0 or curr >= prev * 1.5) and curr > prev:
            if prev == 0:
                msg = f"{label} : {curr} détection(s) cette semaine (aucune la semaine dernière)"
            else:
                pct = int(((curr - prev) / prev) * 100)
                msg = f"{label} : +{pct}% cette semaine ({curr} vs {prev})"

            trend_alerts.append({
                "type":        "trend",
                "category":    key,
                "severity":    severity,
                "message":     msg,
                "current_week": curr,
                "prev_week":    prev
            })

    # ---- Maladies : tendance depuis report_json ----
    def disease_count_in_range(start, end):
        scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.created_at >= start,
            Scan.created_at <  end,
            Scan.report_json != None
        ).all()
        total = 0
        for s in scans:
            try:
                report   = json.loads(s.report_json)
                diseases = report.get("health", {}).get("diseases", [])
                total   += sum(
                    1 for d in diseases
                    if d.strip().lower() not in ["aucune", "aucun", "none", "aucune maladie", "-", ""]
                )
            except Exception:
                pass
        return total

    curr_dis = disease_count_in_range(week_start, now)
    prev_dis = disease_count_in_range(prev_week_start, week_start)

    if curr_dis >= 2 and (prev_dis == 0 or curr_dis >= prev_dis * 1.5) and curr_dis > prev_dis:
        if prev_dis == 0:
            msg = f"Maladies détectées : {curr_dis} cette semaine (aucune la semaine dernière)"
        else:
            pct = int(((curr_dis - prev_dis) / prev_dis) * 100)
            msg = f"Maladies détectées : +{pct}% cette semaine ({curr_dis} vs {prev_dis})"
        trend_alerts.append({
            "type":         "trend",
            "category":     "disease",
            "severity":     "danger",
            "message":      msg,
            "current_week": curr_dis,
            "prev_week":    prev_dis
        })

    return {
        "alerts":       alerts,
        "count":        len(alerts),
        "trend_alerts": trend_alerts
    }


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


# ============================================================
# STATISTIQUES GLOBALES ANONYMISÉES
# Agrégation sur TOUS les utilisateurs — aucune donnée personnelle
# ============================================================

@router.get("/global/summary")
def get_global_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Statistiques globales anonymisées sur l'ensemble des utilisateurs.
    Aucune donnée personnelle : uniquement des comptages agrégés.
    """
    total_scans      = db.query(func.count(Scan.id)).scalar() or 0
    unique_plants    = db.query(func.count(func.distinct(Scan.plant_scientific_name))).scalar() or 0
    toxic_count      = db.query(func.count(Scan.id)).filter(Scan.is_toxic     == True).scalar() or 0
    edible_count     = db.query(func.count(Scan.id)).filter(Scan.is_edible    == True).scalar() or 0
    medicinal_count  = db.query(func.count(Scan.id)).filter(Scan.is_medicinal == True).scalar() or 0
    invasive_count   = db.query(func.count(Scan.id)).filter(Scan.is_invasive  == True).scalar() or 0

    return {
        "total_scans":            total_scans,
        "unique_plants":          unique_plants,
        "toxic_plants_count":     toxic_count,
        "edible_plants_count":    edible_count,
        "medicinal_plants_count": medicinal_count,
        "invasive_plants_count":  invasive_count,
    }


@router.get("/global/top-plants")
def get_global_top_plants(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Plantes les plus scannées sur toute la plateforme (tous utilisateurs).
    """
    results = db.query(
        Scan.plant_name,
        Scan.plant_scientific_name,
        func.count(Scan.id).label("scan_count")
    ).group_by(
        Scan.plant_name,
        Scan.plant_scientific_name
    ).order_by(desc("scan_count")).limit(limit).all()

    return [
        {
            "plant_name":    row.plant_name or "Inconnue",
            "scientific_name": row.plant_scientific_name or "",
            "scan_count":    row.scan_count
        }
        for row in results
    ]


@router.get("/global/diseases")
def get_global_diseases(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Maladies les plus fréquentes sur toute la plateforme (tous utilisateurs).
    Anonymisé : aucun lien avec les utilisateurs.
    """
    scans = db.query(Scan).filter(Scan.report_json != None).all()

    disease_counts = {}
    for scan in scans:
        try:
            report   = json.loads(scan.report_json)
            diseases = report.get("health", {}).get("diseases", [])
            for disease in diseases:
                clean = disease.strip()
                if clean and clean.lower() not in ["aucune", "aucun", "none", "aucune maladie", "-"]:
                    disease_counts[clean] = disease_counts.get(clean, 0) + 1
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue

    sorted_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"disease": name, "count": count} for name, count in sorted_diseases]


@router.get("/global/distribution")
def get_global_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Répartition comestible / toxique / médicinal / invasif — tous utilisateurs.
    """
    total    = db.query(func.count(Scan.id)).scalar() or 1
    edible   = db.query(func.count(Scan.id)).filter(Scan.is_edible    == True).scalar() or 0
    toxic    = db.query(func.count(Scan.id)).filter(Scan.is_toxic     == True).scalar() or 0
    medicinal= db.query(func.count(Scan.id)).filter(Scan.is_medicinal == True).scalar() or 0
    invasive = db.query(func.count(Scan.id)).filter(Scan.is_invasive  == True).scalar() or 0

    return {
        "labels": ["Comestibles", "Toxiques", "Médicinales", "Invasives"],
        "values": [edible, toxic, medicinal, invasive],
        "total":  total
    }


@router.get("/global/regions-at-risk")
def get_global_regions_at_risk(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Zones géographiques avec le plus de plantes toxiques ou invasives.
    Anonymisé : les coordonnées GPS sont arrondies à 1 décimale (≈ 10 km).
    """
    scans = db.query(Scan).filter(
        Scan.latitude  != None,
        Scan.longitude != None,
        (Scan.is_invasive == True) | (Scan.is_toxic == True)
    ).all()

    # Arrondir les coordonnées à 1 décimale pour anonymiser (~zone de 10 km)
    zone_counts = {}
    for scan in scans:
        lat_r = round(scan.latitude,  1)
        lng_r = round(scan.longitude, 1)
        key   = f"{lat_r},{lng_r}"
        if key not in zone_counts:
            zone_counts[key] = {
                "lat": lat_r, "lng": lng_r,
                "toxic": 0, "invasive": 0, "total": 0
            }
        if scan.is_toxic:    zone_counts[key]["toxic"]    += 1
        if scan.is_invasive: zone_counts[key]["invasive"] += 1
        zone_counts[key]["total"] += 1

    zones = sorted(zone_counts.values(), key=lambda z: z["total"], reverse=True)
    return {"zones": zones, "total_zones": len(zones)}
