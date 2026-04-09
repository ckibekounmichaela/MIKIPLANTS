# ============================================================
# FICHIER : backend/services/plant_lookup.py
# RÔLE    : Rechercher une plante dans notre catalogue local
#           pour enrichir les analyses PlantNet + Groq
#
# CONCEPT :
#   Après que PlantNet identifie une plante, on interroge
#   notre propre base de données. Si on trouve une correspondance,
#   on retourne toutes nos données locales sur cette plante
#   (habitats en CI, usages locaux, noms en dioula/baoulé...).
#   Ces données servent ensuite de contexte fiable pour Groq.
#
# STRATÉGIE DE RECHERCHE (du plus précis au plus large) :
#   1. Nom scientifique exact          → correspondance certaine
#   2. Genre botanique commun          → même famille de plantes
#   3. Famille botanique               → enrichissement partiel
#   4. Nom commun (recherche floue)    → dernier recours
# ============================================================

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import Plant


def find_local_plant(db: Session, plantnet_result: dict) -> dict | None:
    """
    Cherche dans notre catalogue la plante identifiée par PlantNet.

    PARAMÈTRES :
        db             : Session SQLAlchemy active
        plantnet_result: Résultat de PlantNet
                         {"plant_name", "scientific_name", "family", "confidence_score"}

    RETOUR :
        Dictionnaire avec les données locales, ou None si aucune correspondance.
    """

    scientific_name = plantnet_result.get("scientific_name", "").strip()
    plant_name      = plantnet_result.get("plant_name", "").strip()
    family          = plantnet_result.get("family", "").strip()

    plant = None

    # ──────────────────────────────────────────────────────────
    # NIVEAU 1 : Correspondance exacte sur le nom scientifique
    # Ex : "Mangifera indica" → trouvé directement
    # ──────────────────────────────────────────────────────────
    if scientific_name:
        plant = db.query(Plant).filter(
            func.lower(Plant.scientific_name) == scientific_name.lower()
        ).first()

    # ──────────────────────────────────────────────────────────
    # NIVEAU 2 : Même genre botanique
    # Ex : "Mangifera sylvatica" → cherche "Mangifera %"
    # Le genre est le premier mot du nom scientifique
    # ──────────────────────────────────────────────────────────
    if not plant and scientific_name and " " in scientific_name:
        genre = scientific_name.split(" ")[0]
        plant = db.query(Plant).filter(
            Plant.scientific_name.ilike(f"{genre} %")
        ).first()

    # ──────────────────────────────────────────────────────────
    # NIVEAU 3 : Même famille botanique
    # Ex : famille "Anacardiaceae" → on prend la première plante
    #      de cette famille dans notre base
    # ──────────────────────────────────────────────────────────
    if not plant and family:
        plant = db.query(Plant).filter(
            func.lower(Plant.family) == family.lower()
        ).first()

    # ──────────────────────────────────────────────────────────
    # NIVEAU 4 : Recherche floue sur le nom commun
    # Ex : "Mango tree" → cherche "mango" dans les noms
    # ──────────────────────────────────────────────────────────
    if not plant and plant_name:
        mots = [m for m in plant_name.lower().split() if len(m) > 3]
        for mot in mots:
            plant = db.query(Plant).filter(
                or_(
                    Plant.name.ilike(f"%{mot}%"),
                    Plant.local_name.ilike(f"%{mot}%"),
                )
            ).first()
            if plant:
                break

    if not plant:
        return None

    # ──────────────────────────────────────────────────────────
    # Retourner un dictionnaire propre avec les données locales
    # ──────────────────────────────────────────────────────────
    return {
        "id":             plant.id,
        "name":           plant.name,
        "local_name":     plant.local_name or "Non renseigné",
        "scientific_name": plant.scientific_name,
        "family":         plant.family or "Non renseignée",
        "description":    plant.description or "",
        "habitat":        plant.habitat or "Non renseigné",
        "regions":        plant.regions or "Non renseignées",
        "is_edible":      plant.is_edible,
        "is_medicinal":   plant.is_medicinal,
        "is_toxic":       plant.is_toxic,
        "is_invasive":    plant.is_invasive,
        "toxicity_level": plant.toxicity_level,
        "culinary_uses":  plant.culinary_uses or "Non documenté",
        "medicinal_uses": plant.medicinal_uses or "Non documenté",
    }


def build_local_context_block(local_data: dict) -> str:
    """
    Transforme les données locales en un bloc texte structuré
    prêt à être injecté dans les prompts Groq.

    EXEMPLE DE SORTIE :
        === DONNÉES LOCALES CÔTE D'IVOIRE ===
        Nom local (dioula/baoulé) : Mangoro
        Habitat en CI             : Zones cultivées, villages
        Régions de CI présentes   : Tout le territoire
        ...
    """
    if not local_data:
        return ""

    edible_str   = "Oui" if local_data["is_edible"]   else "Non"
    medicinal_str= "Oui" if local_data["is_medicinal"] else "Non"
    toxic_str    = "Oui" if local_data["is_toxic"]     else "Non"
    invasive_str = "Oui" if local_data["is_invasive"]  else "Non"

    return f"""
=== DONNÉES DE NOTRE BASE LOCALE (Côte d'Ivoire) ===
Nom local (dioula/baoulé)  : {local_data['local_name']}
Habitat en Côte d'Ivoire   : {local_data['habitat']}
Régions de CI présentes    : {local_data['regions']}
Comestible                 : {edible_str}
Médicinal                  : {medicinal_str}
Toxique                    : {toxic_str}
Espèce invasive            : {invasive_str}
Niveau de toxicité         : {local_data['toxicity_level']}
Usages culinaires locaux   : {local_data['culinary_uses']}
Usages médicinaux locaux   : {local_data['medicinal_uses']}
Description locale         : {local_data['description'][:300] + '...' if len(local_data.get('description','')) > 300 else local_data['description']}
=====================================================
Utilise PRIORITAIREMENT ces données locales vérifiées pour enrichir
et préciser ton analyse. Elles proviennent d'une base botanique
spécialisée Côte d'Ivoire / Afrique de l'Ouest.
"""
