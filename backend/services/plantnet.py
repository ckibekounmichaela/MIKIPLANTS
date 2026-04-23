# ============================================================
# FICHIER : backend/services/plantnet.py
# RÔLE    : Communiquer avec l'API PlantNet pour identifier les plantes
#
# CONCEPT POUR DÉBUTANT :
#   PlantNet est une base de données botanique mondiale.
#   Son API permet d'envoyer une photo de plante et de recevoir
#   en retour le nom scientifique, la famille, et un score
#   de confiance (probabilité que l'identification soit correcte).
#
#   Documentation officielle : https://my.plantnet.org/doc/openapi
# ============================================================

import os
import logging
import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")

# URL de base de l'API PlantNet
# "all" signifie qu'on cherche dans toutes les flores du monde
PLANTNET_BASE_URL = "https://my-api.plantnet.org/v2/identify/all"


async def identify_plant(image_bytes: bytes, image_filename: str) -> dict:
    """
    Envoie une image à l'API PlantNet et retourne l'identification.

    PARAMÈTRES :
        image_bytes    : Le contenu de l'image en bytes (données brutes)
        image_filename : Le nom du fichier image (ex: "plante.jpg")

    RETOUR :
        Un dictionnaire avec les informations de la plante identifiée.
        En cas d'erreur, retourne un dictionnaire avec des valeurs par défaut.

    EXEMPLE DE RETOUR :
        {
            "plant_name": "Tomate",
            "scientific_name": "Solanum lycopersicum",
            "family": "Solanaceae",
            "confidence_score": 0.94,
            "success": True
        }
    """

    # Vérifier que la clé API est configurée
    if not PLANTNET_API_KEY:
        logger.error("Clé API PlantNet manquante dans le fichier .env")
        return _default_result(success=False, error="Clé API PlantNet non configurée")

    # -------------------------------------------------------
    # Construire la requête HTTP vers PlantNet
    # On envoie l'image en "multipart/form-data"
    # C'est le même format qu'un formulaire HTML avec un input file
    # -------------------------------------------------------
    try:
        # Paramètres de la requête (dans l'URL)
        params = {
            "api-key": PLANTNET_API_KEY,
            "lang": "fr",           # Réponse en français
            "include-related-images": "false"  # On n'a pas besoin des images similaires
        }

        # Détecter le vrai Content-Type selon l'extension du fichier
        ext = image_filename.rsplit(".", 1)[-1].lower() if "." in image_filename else "jpg"
        mime_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                      "png": "image/png", "webp": "image/webp"}
        mime_type = mime_types.get(ext, "image/jpeg")

        # Fichier à envoyer (l'image de la plante)
        files = {
            "images": (image_filename, image_bytes, mime_type),
        }

        # IMPORTANT : organs doit etre une STRING, pas une liste
        # httpx ne serialise pas les listes correctement en form-data
        data = {
            "organs": "auto"
        }

        # Utiliser httpx pour faire une requête HTTP asynchrone
        # async with : on ouvre une connexion et elle se ferme automatiquement
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                PLANTNET_BASE_URL,
                params=params,
                files=files,
                data=data
            )

        # -------------------------------------------------------
        # Vérifier si la requête a réussi
        # HTTP 200 = succès, 400+ = erreur client, 500+ = erreur serveur
        # -------------------------------------------------------
        if response.status_code != 200:
            logger.error(f"PlantNet: Code {response.status_code} - {response.text}")
            return _default_result(
                success=False,
                error=f"PlantNet a retourné une erreur: {response.status_code}"
            )

        # Convertir la réponse JSON en dictionnaire Python
        data_response = response.json()

        # -------------------------------------------------------
        # Extraire le premier résultat (le plus probable)
        # PlantNet renvoie une liste de résultats triés par score
        # -------------------------------------------------------
        results = data_response.get("results", [])

        if not results:
            return _default_result(success=False, error="Aucune plante identifiée")

        # Prendre le meilleur résultat (index 0 = le plus probable)
        best_result = results[0]

        # Extraire les informations de la plante
        species = best_result.get("species", {})

        # Nom scientifique complet (genre + espèce)
        scientific_name = species.get("scientificNameWithoutAuthor", "Inconnue")

        # Nom commun en français (si disponible)
        common_names = species.get("commonNames", [])
        plant_name = common_names[0] if common_names else scientific_name

        # Famille botanique
        family = species.get("family", {}).get("scientificNameWithoutAuthor", "Inconnue")

        confidence_score = round(best_result.get("score", 0.0), 4)

        return {
            "plant_name": plant_name,
            "scientific_name": scientific_name,
            "family": family,
            "confidence_score": confidence_score,
            "success": True
        }

    except httpx.TimeoutException:
        # La requête a pris trop de temps (> 30 secondes)
        logger.error("PlantNet: Timeout - le serveur n'a pas répondu à temps")
        return _default_result(success=False, error="Timeout lors de l'appel à PlantNet")

    except Exception as e:
        # Toute autre erreur inattendue
        logger.error(f"PlantNet: erreur inattendue : {str(e)}")
        return _default_result(success=False, error=str(e))


def _default_result(success: bool, error: str = "") -> dict:
    """
    Retourne un résultat par défaut quand l'identification échoue.
    Permet à l'application de continuer même si PlantNet est indisponible.
    """
    return {
        "plant_name": "Plante non identifiée",
        "scientific_name": "Espèce inconnue",
        "family": "Famille inconnue",
        "confidence_score": 0.0,
        "success": success,
        "error": error
    }
