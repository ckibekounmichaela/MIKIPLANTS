import csv
import io
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

def extract_diseases(scan) -> list:
    """Extrait les maladies depuis le rapport JSON d'un scan."""
    if not scan.report_json:
        return []
    try:
        report    = json.loads(scan.report_json)
        diseases  = report.get("health", {}).get("diseases", [])
        return [
            d.strip() for d in diseases
            if d.strip().lower() not in ["aucune", "aucun", "none", "aucune maladie", "-", ""]
        ]
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def diseases_as_string(scan) -> str:
    """Retourne les maladies d'un scan sous forme de chaîne pour le CSV."""
    return " | ".join(extract_diseases(scan))

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

    total_scans = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id
    ).scalar()

    unique_plants = db.query(func.count(func.distinct(Scan.plant_scientific_name))).filter(
        Scan.user_id == current_user.id
    ).scalar()

    toxic_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_toxic == True
    ).scalar()

    edible_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_edible == True
    ).scalar()

    medicinal_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_medicinal == True
    ).scalar()

    invasive_count = db.query(func.count(Scan.id)).filter(
        Scan.user_id == current_user.id,
        Scan.is_invasive == True
    ).scalar()

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
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer le classement des plantes les plus scannées.
    """


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
    start_date = datetime.utcnow() - timedelta(days=days)

    scans = db.query(Scan).filter(
        Scan.user_id == current_user.id,
        Scan.created_at >= start_date
    ).order_by(Scan.created_at.asc()).all()

    daily_counts = {}
    for scan in scans:
        day_key = scan.created_at.strftime("%Y-%m-%d")
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

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
    limit: int = Query(10, ge=1, le=50),
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
        for disease in extract_diseases(scan):
            disease_counts[disease] = disease_counts.get(disease, 0) + 1

    sorted_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"disease": name, "count": count} for name, count in sorted_diseases]


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
    limit: int = Query(10, ge=1, le=50),
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
    limit: int = Query(10, ge=1, le=50),
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
        for disease in extract_diseases(scan):
            disease_counts[disease] = disease_counts.get(disease, 0) + 1

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



@router.get("/is-admin")
def is_admin(
    current_user: User = Depends(get_current_user)
):
    """Retourne si l'utilisateur connecté est administrateur."""
    return {"is_admin": bool(ADMIN_EMAIL and current_user.email.lower() == ADMIN_EMAIL.lower())}


_CSV_INJECTION_CHARS = ("=", "+", "-", "@", "\t", "\r")

def _sanitize_csv_value(value) -> str:
    """Protège contre l'injection CSV (formules Excel/LibreOffice)."""
    s = str(value) if value is not None else ""
    if s and s[0] in _CSV_INJECTION_CHARS:
        s = "'" + s  # préfixer par apostrophe neutralise la formule
    return s


def _build_csv(rows: list[dict], fieldnames: list[str]) -> io.BytesIO:
    """Construit un fichier CSV en mémoire avec BOM UTF-8 (lisible par Excel)."""
    sanitized = [
        {k: _sanitize_csv_value(v) for k, v in row.items()}
        for row in rows
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(sanitized)
    # BOM UTF-8 (\ufeff) permet à Excel de détecter l'encodage automatiquement
    # sans BOM, les accents et caractères spéciaux s'affichent mal sur Windows
    bytes_output = io.BytesIO()
    bytes_output.write(b"\xef\xbb\xbf")  # BOM UTF-8
    bytes_output.write(output.getvalue().encode("utf-8"))
    bytes_output.seek(0)
    return bytes_output


@router.get("/export/mes-scans")
def export_my_scans_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Télécharger TOUS les scans de l'utilisateur connecté en fichier CSV.
    Inclut : date, plante, nom scientifique, famille, score de confiance,
             comestible, toxique, médicinal, invasif, toxicité, maladies, GPS.
    """
    scans = db.query(Scan).filter(
        Scan.user_id == current_user.id
    ).order_by(Scan.created_at.desc()).all()

    fieldnames = [
        "id", "date", "plante", "nom_scientifique", "famille",
        "score_confiance_%", "comestible", "toxique", "medicinal",
        "invasif", "niveau_toxicite", "maladies", "latitude", "longitude"
    ]

    rows = []
    for scan in scans:
        rows.append({
            "id":                  scan.id,
            "date":                scan.created_at.strftime("%Y-%m-%d %H:%M"),
            "plante":              scan.plant_name or "",
            "nom_scientifique":    scan.plant_scientific_name or "",
            "famille":             scan.plant_family or "",
            "score_confiance_%":   round((scan.confidence_score or 0) * 100, 1),
            "comestible":          "Oui" if scan.is_edible   else "Non",
            "toxique":             "Oui" if scan.is_toxic    else "Non",
            "medicinal":           "Oui" if scan.is_medicinal else "Non",
            "invasif":             "Oui" if scan.is_invasive  else "Non",
            "niveau_toxicite":     scan.toxicity_level or "aucun",
            "maladies":            diseases_as_string(scan),
            "latitude":            scan.latitude  or "",
            "longitude":           scan.longitude or "",
        })

    csv_file = _build_csv(rows, fieldnames)
    filename  = f"mes_scans_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        csv_file,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/tous-les-scans")
def export_all_scans_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Télécharger les scans de TOUS les utilisateurs en CSV anonymisé.
    Réservé à l'administrateur (ADMIN_EMAIL dans .env).
    Données personnelles exclues : email, username remplacés par user_id anonyme.
    Coordonnées GPS arrondies à 1 décimale (~10 km) pour la confidentialité.
    """
    if not ADMIN_EMAIL or current_user.email.lower() != ADMIN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé à l'administrateur."
        )

    scans = db.query(Scan).order_by(Scan.created_at.desc()).all()

    user_id_map: dict[int, int] = {}
    counter = 1
    for scan in scans:
        if scan.user_id not in user_id_map:
            user_id_map[scan.user_id] = counter
            counter += 1

    fieldnames = [
        "scan_id", "utilisateur_anonyme", "date",
        "plante", "nom_scientifique", "famille",
        "score_confiance_%", "comestible", "toxique", "medicinal",
        "invasif", "niveau_toxicite", "maladies",
        "zone_lat", "zone_lng"   # GPS arrondi à 1 décimale
    ]

    rows = []
    for scan in scans:

        rows.append({
            "scan_id":              scan.id,
            "utilisateur_anonyme":  f"Utilisateur #{user_id_map[scan.user_id]}",
            "date":                 scan.created_at.strftime("%Y-%m-%d"),
            "plante":               scan.plant_name or "",
            "nom_scientifique":     scan.plant_scientific_name or "",
            "famille":              scan.plant_family or "",
            "score_confiance_%":    round((scan.confidence_score or 0) * 100, 1),
            "comestible":           "Oui" if scan.is_edible    else "Non",
            "toxique":              "Oui" if scan.is_toxic     else "Non",
            "medicinal":            "Oui" if scan.is_medicinal  else "Non",
            "invasif":              "Oui" if scan.is_invasive   else "Non",
            "niveau_toxicite":      scan.toxicity_level or "aucun",
            "maladies":             diseases_as_string(scan),
            "zone_lat":             round(scan.latitude,  1) if scan.latitude  else "",
            "zone_lng":             round(scan.longitude, 1) if scan.longitude else "",
        })

    csv_file = _build_csv(rows, fieldnames)
    filename  = f"tous_scans_anonymises_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        csv_file,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
