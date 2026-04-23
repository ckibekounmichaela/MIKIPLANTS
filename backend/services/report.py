def extract_metadata_from_report(report: dict) -> dict:
    """
    Extrait les métadonnées importantes du rapport JSON.

    Ces métadonnées sont stockées dans des colonnes dédiées
    de la table "scans" pour faciliter les requêtes SQL.
    Par exemple, pour filtrer tous les scans de plantes toxiques,
    on fait : db.query(Scan).filter(Scan.is_toxic == True)

    PARAMÈTRES :
        report : Le rapport complet généré par Groq (dictionnaire)

    RETOUR :
        Un dictionnaire avec les métadonnées extraites.

    EXEMPLE :
        {
            "is_edible": True,
            "is_toxic": False,
            "is_medicinal": True,
            "is_invasive": False,
            "toxicity_level": "aucun"
        }
    """

    metadata = {
        "is_edible": False,
        "is_toxic": False,
        "is_medicinal": False,
        "is_invasive": False,
        "toxicity_level": "aucun"
    }

    # -------------------------------------------------------
    # Extraire les données de chaque section du rapport
    # On utilise .get() pour éviter les erreurs si une clé manque
    # Ex: report.get("edibility", {}) retourne {} si "edibility" n'existe pas
    # -------------------------------------------------------

    # Section comestibilité
    edibility = report.get("edibility", {})
    verdict = edibility.get("verdict", "non").lower()
    # La plante est comestible si le verdict est "oui" ou "partiel"
    metadata["is_edible"] = verdict in ["oui", "partiel", "yes", "partial"]

    # Section toxicité
    toxicity = report.get("toxicity", {})
    toxicity_level = toxicity.get("level", "aucun").lower()
    metadata["toxicity_level"] = toxicity_level
    # La plante est toxique si le niveau n'est pas "aucun" ou "inconnu"
    metadata["is_toxic"] = toxicity_level not in ["aucun", "inconnu", "none", ""]

    # Section médicinale
    medicinal = report.get("medicinal", {})
    uses = medicinal.get("uses", [])
    # La plante est médicinale si elle a au moins un usage documenté
    # et que ce n'est pas juste "Aucun" ou "Information non disponible"
    metadata["is_medicinal"] = (
        len(uses) > 0 and
        uses[0].lower() not in ["aucun", "information non disponible", "none"]
    )

    # Section environnement
    environment = report.get("environment", {})
    metadata["is_invasive"] = environment.get("invasive", False)

    return metadata
