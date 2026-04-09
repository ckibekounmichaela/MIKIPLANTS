# ============================================================
# FICHIER : backend/routers/scan.py
# RÔLE    : Endpoints pour l'analyse de plantes et l'historique
#
# FLUX D'ANALYSE :
#   Client → envoie image
#   → PlantNet identifie la plante
#   → Groq génère le rapport
#   → On extrait les métadonnées
#   → On sauvegarde tout en BD
#   → On retourne le rapport complet
# ============================================================

import os
import uuid
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from PIL import Image
import io

from database import get_db
from models import Scan, User
from schemas import ScanResponse, ScanListItem, LocalPlantMatch
from routers.auth import get_current_user
from services import plantnet, groq_ai, report as report_service
from services.plant_lookup import find_local_plant, build_local_context_block

router = APIRouter()

# Dossier où stocker les images uploadées
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../uploads")
# Taille maximale autorisée pour une image (5 MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB en bytes
# Types de fichiers autorisés
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/analyze", response_model=ScanResponse)
async def analyze_plant(
    image: UploadFile = File(...),              # Fichier image obligatoire
    latitude: Optional[float] = Form(None),    # Latitude GPS (optionnelle)
    longitude: Optional[float] = Form(None),   # Longitude GPS (optionnelle)
    current_user: User = Depends(get_current_user),  # Utilisateur connecté
    db: Session = Depends(get_db)
):
    """
    Analyser une plante à partir d'une photo.

    C'est l'endpoint principal de l'application.
    Il orchestre tout le pipeline d'analyse :
    PlantNet → Groq → Sauvegarde → Réponse

    PARAMÈTRES (form-data) :
        image     : Le fichier image de la plante
        latitude  : Coordonnée GPS (optionnelle)
        longitude : Coordonnée GPS (optionnelle)
    """

    # -------------------------------------------------------
    # ÉTAPE 1 : Valider le fichier uploadé
    # -------------------------------------------------------

    # Vérifier le type de fichier
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté: {image.content_type}. "
                   f"Utilisez JPG, PNG ou WebP."
        )

    # Lire le contenu de l'image
    image_bytes = await image.read()

    # Vérifier la taille du fichier
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="L'image est trop volumineuse. Taille maximum : 5 MB."
        )

    # Vérifier que c'est une vraie image (pas un fichier malveillant renommé)
    # NOTE : on utilise img.load() et non img.verify()
    # verify() ne lit que l'en-tête et laisse l'objet dans un état inutilisable.
    # load() décode l'image complète — plus fiable pour détecter les fichiers corrompus.
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()  # Décode l'image entière pour s'assurer qu'elle est valide
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Le fichier envoyé n'est pas une image valide."
        )

    # -------------------------------------------------------
    # ÉTAPE 2 : Sauvegarder l'image sur le disque
    # On génère un nom unique avec UUID pour éviter les collisions
    # -------------------------------------------------------
    file_extension = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    # Chemin relatif pour l'URL (accessible via /uploads/...)
    image_url = f"uploads/{unique_filename}"

    # -------------------------------------------------------
    # ÉTAPE 3 : Identifier la plante avec PlantNet
    # -------------------------------------------------------
    plantnet_result = await plantnet.identify_plant(image_bytes, unique_filename)

    # -------------------------------------------------------
    # ÉTAPE 3.5 : Rechercher la plante dans notre catalogue local
    # Si on la trouve, on construit un bloc de contexte enrichi
    # qui sera injecté dans le prompt Groq pour un rapport
    # beaucoup plus précis sur la réalité ivoirienne.
    # -------------------------------------------------------
    local_data    = find_local_plant(db, plantnet_result)
    local_context = build_local_context_block(local_data) if local_data else ""

    if local_data:
        print(f"[LOOKUP] Correspondance trouvée : {local_data['scientific_name']} (ID {local_data['id']})")
    else:
        print(f"[LOOKUP] Aucune correspondance locale pour : {plantnet_result.get('scientific_name')}")

    # -------------------------------------------------------
    # ÉTAPE 4 : Générer le rapport avec Groq IA
    # On passe les résultats PlantNet + le contexte local
    # -------------------------------------------------------
    report_data = await groq_ai.generate_plant_report(plantnet_result, local_context=local_context)

    # -------------------------------------------------------
    # ÉTAPE 5 : Extraire les métadonnées du rapport
    # (is_toxic, is_edible, etc. pour les filtres et stats)
    # -------------------------------------------------------
    metadata = report_service.extract_metadata_from_report(report_data)

    # -------------------------------------------------------
    # ÉTAPE 6 : Sauvegarder tout en base de données
    # -------------------------------------------------------
    new_scan = Scan(
        user_id=current_user.id,
        image_path=image_url,
        plant_name=plantnet_result.get("plant_name", "Inconnue"),
        plant_scientific_name=plantnet_result.get("scientific_name", ""),
        plant_family=plantnet_result.get("family", ""),
        confidence_score=plantnet_result.get("confidence_score", 0.0),
        report_json=json.dumps(report_data, ensure_ascii=False),
        latitude=latitude,
        longitude=longitude,
        is_edible=metadata["is_edible"],
        is_toxic=metadata["is_toxic"],
        is_medicinal=metadata["is_medicinal"],
        is_invasive=metadata["is_invasive"],
        toxicity_level=metadata["toxicity_level"],
        local_plant_id=local_data["id"] if local_data else None,
        local_plant_name=local_data["name"] if local_data else None,
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # -------------------------------------------------------
    # ÉTAPE 7 : Construire et retourner la réponse
    # On convertit le JSON string en dictionnaire pour la réponse
    # -------------------------------------------------------
    # Construire l'objet local_match si une correspondance a été trouvée
    local_match_obj = None
    if local_data:
        local_match_obj = LocalPlantMatch(
            id=local_data["id"],
            name=local_data["name"],
            local_name=local_data.get("local_name"),
            scientific_name=local_data["scientific_name"],
            habitat=local_data.get("habitat"),
            regions=local_data.get("regions"),
            culinary_uses=local_data.get("culinary_uses"),
            medicinal_uses=local_data.get("medicinal_uses"),
        )

    return ScanResponse(
        id=new_scan.id,
        plant_name=new_scan.plant_name,
        plant_scientific_name=new_scan.plant_scientific_name,
        plant_family=new_scan.plant_family,
        confidence_score=new_scan.confidence_score,
        image_path=new_scan.image_path,
        report=json.loads(new_scan.report_json) if new_scan.report_json else {},
        is_edible=new_scan.is_edible,
        is_toxic=new_scan.is_toxic,
        is_medicinal=new_scan.is_medicinal,
        is_invasive=new_scan.is_invasive,
        toxicity_level=new_scan.toxicity_level,
        local_match=local_match_obj,
        created_at=new_scan.created_at
    )


@router.get("/history", response_model=List[ScanListItem])
def get_scan_history(
    page: int = 1,              # Numéro de page (commence à 1)
    limit: int = 12,            # Nombre de scans par page
    filter_type: Optional[str] = None,  # Filtre: "toxic", "edible", "medicinal", "invasive"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'historique des scans de l'utilisateur connecté.

    PARAMÈTRES (dans l'URL) :
        page        : Numéro de page (défaut: 1)
        limit       : Scans par page (défaut: 12)
        filter_type : Filtrer par type de plante (optionnel)

    EXEMPLE D'URL : GET /api/scan/history?page=2&limit=10&filter_type=toxic
    """

    # Construire la requête de base
    query = db.query(Scan).filter(Scan.user_id == current_user.id)

    # Appliquer le filtre si demandé
    if filter_type == "toxic":
        query = query.filter(Scan.is_toxic == True)
    elif filter_type == "edible":
        query = query.filter(Scan.is_edible == True)
    elif filter_type == "medicinal":
        query = query.filter(Scan.is_medicinal == True)
    elif filter_type == "invasive":
        query = query.filter(Scan.is_invasive == True)

    # Trier par date décroissante (plus récent en premier)
    query = query.order_by(Scan.created_at.desc())

    # Calculer l'offset pour la pagination
    # Si page=2 et limit=12, on saute les 12 premiers résultats
    offset = (page - 1) * limit
    scans = query.offset(offset).limit(limit).all()

    return scans


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_detail(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer le détail complet d'un scan spécifique.

    PARAMÈTRE (dans l'URL) :
        scan_id : L'identifiant du scan (ex: /api/scan/42)
    """
    # Chercher le scan
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.user_id == current_user.id  # Sécurité : on ne peut voir que ses propres scans
    ).first()

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan non trouvé ou accès non autorisé."
        )

    # Reconstruire local_match depuis la BD si disponible
    local_match_obj = None
    if scan.local_plant_id:
        from models import Plant
        lp = db.query(Plant).filter(Plant.id == scan.local_plant_id).first()
        if lp:
            local_match_obj = LocalPlantMatch(
                id=lp.id,
                name=lp.name,
                local_name=lp.local_name,
                scientific_name=lp.scientific_name,
                habitat=lp.habitat,
                regions=lp.regions,
                culinary_uses=lp.culinary_uses,
                medicinal_uses=lp.medicinal_uses,
            )

    return ScanResponse(
        id=scan.id,
        plant_name=scan.plant_name,
        plant_scientific_name=scan.plant_scientific_name,
        plant_family=scan.plant_family,
        confidence_score=scan.confidence_score,
        image_path=scan.image_path,
        report=json.loads(scan.report_json) if scan.report_json else {},
        is_edible=scan.is_edible,
        is_toxic=scan.is_toxic,
        is_medicinal=scan.is_medicinal,
        is_invasive=scan.is_invasive,
        toxicity_level=scan.toxicity_level,
        local_match=local_match_obj,
        created_at=scan.created_at
    )


@router.delete("/{scan_id}", status_code=204)
def delete_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer un scan et son image associée.
    Un utilisateur ne peut supprimer que ses propres scans.
    """
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.user_id == current_user.id
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan non trouvé.")

    # Supprimer l'image du disque si elle existe
    if scan.image_path and os.path.exists(f"../{scan.image_path}"):
        os.remove(f"../{scan.image_path}")

    # Supprimer le scan de la BD (les messages de chat sont supprimés en cascade)
    db.delete(scan)
    db.commit()

    # 204 No Content = succès sans corps de réponse
    return None
