from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Plant
from schemas import PlantResponse, PlantListItem, PlantCatalogStats

router = APIRouter()


@router.get("/stats", response_model=PlantCatalogStats)
def get_catalog_stats(db: Session = Depends(get_db)):
    """
    Statistiques globales du catalogue de plantes.
    Accessible sans authentification.
    """
    total      = db.query(func.count(Plant.id)).scalar() or 0
    edible     = db.query(func.count(Plant.id)).filter(Plant.is_edible    == True).scalar() or 0
    medicinal  = db.query(func.count(Plant.id)).filter(Plant.is_medicinal == True).scalar() or 0
    toxic      = db.query(func.count(Plant.id)).filter(Plant.is_toxic     == True).scalar() or 0
    invasive   = db.query(func.count(Plant.id)).filter(Plant.is_invasive  == True).scalar() or 0

    return PlantCatalogStats(
        total=total,
        edible=edible,
        medicinal=medicinal,
        toxic=toxic,
        invasive=invasive,
    )


@router.get("", response_model=List[PlantListItem])
def list_plants(
    search: Optional[str] = Query(None, description="Recherche par nom, nom local ou nom scientifique"),
    is_edible:   Optional[bool] = Query(None, description="Filtrer les plantes comestibles"),
    is_medicinal: Optional[bool] = Query(None, description="Filtrer les plantes médicinales"),
    is_toxic:    Optional[bool] = Query(None, description="Filtrer les plantes toxiques"),
    is_invasive: Optional[bool] = Query(None, description="Filtrer les plantes invasives"),
    skip: int = Query(0,  ge=0,   description="Nombre de résultats à ignorer (pagination)"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """
    Lister les plantes du catalogue avec filtres optionnels.
    Accessible sans authentification.
    """
    query = db.query(Plant)

    # Recherche textuelle sur nom, nom local et nom scientifique
    if search:
        terme = f"%{search}%"
        query = query.filter(
            or_(
                Plant.name.ilike(terme),
                Plant.local_name.ilike(terme),
                Plant.scientific_name.ilike(terme),
                Plant.family.ilike(terme),
            )
        )

    if is_edible is not None:
        query = query.filter(Plant.is_edible == is_edible)
    if is_medicinal is not None:
        query = query.filter(Plant.is_medicinal == is_medicinal)
    if is_toxic is not None:
        query = query.filter(Plant.is_toxic == is_toxic)
    if is_invasive is not None:
        query = query.filter(Plant.is_invasive == is_invasive)

    return query.order_by(Plant.name).offset(skip).limit(limit).all()


@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    """
    Récupérer le détail complet d'une plante par son ID.
    Accessible sans authentification.
    """
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plante introuvable")
    return plant
