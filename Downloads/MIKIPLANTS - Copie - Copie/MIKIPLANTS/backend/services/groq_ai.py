# ============================================================
# FICHIER : backend/services/groq_ai.py
# RÔLE    : Communiquer avec l'API Groq pour générer les rapports
#           et répondre aux questions de l'agent conversationnel
#
# CONCEPT POUR DÉBUTANT :
#   Groq est un service d'IA ultra-rapide qui fait tourner
#   des modèles de langage open-source comme LLaMA 3.
#   On lui envoie un "prompt" (instruction) et il génère
#   une réponse textuelle.
#
#   Inscription gratuite : https://console.groq.com/
#   Modèles disponibles  : https://console.groq.com/docs/models
# ============================================================

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Récupérer les configurations depuis .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Initialiser le client Groq
# Ce client sera réutilisé pour tous les appels à l'API
client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# GÉNÉRATION DU RAPPORT COMPLET
# ============================================================

async def generate_plant_report(plant_data: dict, local_context: str = "") -> dict:
    """
    Génère un rapport complet sur une plante en utilisant l'IA Groq.

    PARAMÈTRES :
        plant_data    : Dictionnaire avec les infos de PlantNet
                        {"plant_name", "scientific_name", "family", "confidence_score"}
        local_context : Bloc texte issu de notre catalogue local (plant_lookup.py).
                        Si fourni, Groq l'utilise en priorité pour enrichir le rapport.

    RETOUR :
        Un dictionnaire structuré avec 5 sections d'analyse.
        Si l'IA échoue, retourne un rapport par défaut.

    COMMENT ÇA MARCHE :
        1. On construit un "prompt" détaillé qui explique à l'IA ce qu'on veut
        2. Si on a des données locales (base CI), on les injecte dans le prompt
        3. On envoie ce prompt à Groq via l'API
        4. Groq répond avec un texte (normalement en JSON)
        5. On parse ce JSON et on le retourne
    """

    # -------------------------------------------------------
    # Construire le prompt (instruction pour l'IA)
    # Un bon prompt = une bonne réponse !
    # -------------------------------------------------------
    prompt = f"""
Tu es un expert botaniste et agronome spécialisé en Afrique de l'Ouest, particulièrement en Côte d'Ivoire.
Une photo de plante vient d'être analysée par l'IA PlantNet :

- Nom commun       : {plant_data['plant_name']}
- Nom scientifique : {plant_data['scientific_name']}
- Famille botanique: {plant_data['family']}
- Score de confiance PlantNet : {plant_data['confidence_score'] * 100:.0f}%

{local_context}

MISSION : Génère un rapport d'analyse complet, précis et sécuritaire sur cette plante en répondant aux 5 questions critiques suivantes.

RÈGLES ABSOLUES :
1. Réponds UNIQUEMENT avec un JSON valide, AUCUN texte avant ou après
2. Sois toujours prudent et mentionne tous les risques potentiels
3. Si une information est incertaine, écris "Information non disponible"
4. Adapte TOUTES les réponses au contexte de l'Afrique de l'Ouest / Côte d'Ivoire
5. Les listes ne doivent JAMAIS être vides, mets au moins ["Aucun connu"] si nécessaire
6. Sois précis et concret, évite les réponses vagues

Génère exactement ce JSON :

{{
  "health": {{
    "status": "Bonne santé OU Maladie possible OU Maladie fréquente",
    "visual_signs": ["signes visuels à observer sur la plante (feuilles, tiges, racines)"],
    "diseases": ["Nom de la maladie (nom scientifique si possible) — symptômes associés"],
    "treatments": ["Traitement NATUREL : description", "Traitement CHIMIQUE : produit recommandé et dosage"]
  }},
  "edibility": {{
    "verdict": "oui OU non OU partiel",
    "edible_parts": ["partie comestible — comment la préparer"],
    "recipes": ["Nom de la recette locale — ingrédients principaux et préparation rapide"],
    "warnings": ["précaution spécifique avant consommation — pourquoi c'est important"]
  }},
  "medicinal": {{
    "uses": ["Usage traditionnel documenté — quelle maladie ou symptôme il traite"],
    "dosage": "posologie précise (quantité, fréquence, durée) ou 'Consulter un professionnel de santé'",
    "preparation": ["méthode de préparation traditionnelle, ex: décoction, infusion, cataplasme"],
    "contraindications": ["contre-indication spécifique — groupe à risque concerné"]
  }},
  "toxicity": {{
    "level": "aucun OU faible OU moyen OU élevé",
    "toxic_parts": ["partie toxique de la plante"],
    "symptoms": ["symptôme précis en cas d'ingestion ou contact — délai d'apparition"],
    "first_aid": "premiers secours détaillés étape par étape"
  }},
  "environment": {{
    "invasive": true,
    "allelopathic": false,
    "allelopathic_detail": "explication de l'effet allélopathique sur les plantes voisines ou 'Non allélopathique'",
    "soil_impact": "impact précis sur la qualité et la composition du sol",
    "agricultural_impact": "impact sur les cultures voisines (positif ou négatif) avec exemples concrets"
  }}
}}
"""

    try:
        # -------------------------------------------------------
        # Appeler l'API Groq
        # messages = liste de messages comme dans une conversation
        # -------------------------------------------------------
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert botaniste. "
                        "Tu réponds TOUJOURS avec un JSON valide et structuré. "
                        "Jamais de texte hors du JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,    # Faible = réponses plus cohérentes et précises
            max_tokens=4096,    # Augmenté pour les rapports détaillés
        )

        # Extraire le texte de la réponse
        response_text = response.choices[0].message.content.strip()

        # -------------------------------------------------------
        # Parser le JSON retourné par l'IA
        # L'IA peut parfois ajouter des ```json ... ``` autour
        # On nettoie ça avant de parser
        # -------------------------------------------------------
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Convertir le texte JSON en dictionnaire Python
        report = json.loads(response_text)
        return report

    except json.JSONDecodeError as e:
        # L'IA n'a pas renvoyé un JSON valide
        print(f"ERREUR: L'IA n'a pas retourné un JSON valide: {e}")
        return _default_report()

    except Exception as e:
        # Toute autre erreur (réseau, clé API invalide, etc.)
        print(f"ERREUR Groq: {str(e)}")
        return _default_report()


# ============================================================
# AGENT CONVERSATIONNEL
# ============================================================

async def chat_with_agent(
    plant_context: dict,
    conversation_history: list,
    user_message: str,
    local_context: str = ""
) -> str:
    """
    Répond à une question de l'utilisateur en tenant compte du contexte
    de la plante analysée et de l'historique de la conversation.

    PARAMÈTRES :
        plant_context        : Informations sur la plante (nom, rapport...)
        conversation_history : Liste des messages précédents [{role, content}]
        user_message         : La nouvelle question de l'utilisateur

    RETOUR :
        La réponse de l'IA sous forme de chaîne de caractères.

    CONCEPT :
        On envoie TOUT l'historique de la conversation à chaque appel.
        Ainsi, l'IA "se souvient" des échanges précédents et peut
        donner des réponses cohérentes et contextualisées.
    """

    # -------------------------------------------------------
    # Créer le message "system" qui définit le comportement de l'IA
    # Ce message est envoyé en premier et donne le contexte global
    # -------------------------------------------------------
    system_message = f"""
Tu es un assistant botaniste expert et bienveillant, spécialisé en Afrique de l'Ouest.
Tu aides l'utilisateur à comprendre la plante qu'il a photographiée.

CONTEXTE DE LA PLANTE ANALYSÉE :
- Nom commun      : {plant_context.get('plant_name', 'Non identifiée')}
- Nom scientifique: {plant_context.get('scientific_name', 'Inconnu')}
- Famille         : {plant_context.get('family', 'Inconnue')}
- Confiance       : {plant_context.get('confidence_score', 0) * 100:.0f}%

RAPPORT D'ANALYSE :
{json.dumps(plant_context.get('report', {}), ensure_ascii=False, indent=2)}

{local_context}

RÈGLES DE COMPORTEMENT :
1. Réponds toujours en français, de manière claire et accessible
2. Sois précis mais prudent, surtout pour les usages médicinaux
3. TOUJOURS rappeler de consulter un professionnel de santé pour usage médical
4. Si la question dépasse tes connaissances, dis-le honnêtement
5. Adapte tes réponses au contexte agricole d'Afrique de l'Ouest
6. En cas de plante toxique, souligne les dangers clairement
7. Garde tes réponses concises (max 300 mots)
"""

    # -------------------------------------------------------
    # Construire la liste de messages pour l'API Groq
    # Format : [système, message1, réponse1, message2, réponse2, ...]
    # -------------------------------------------------------
    messages = [{"role": "system", "content": system_message}]

    # Ajouter l'historique de la conversation
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Ajouter le nouveau message de l'utilisateur
    messages.append({"role": "user", "content": user_message})

    try:
        # Appeler l'API Groq
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,    # Un peu plus créatif que pour les rapports
            max_tokens=1024,
        )

        # Extraire et retourner la réponse
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"ERREUR agent Groq: {str(e)}")
        return (
            "Désolé, je rencontre un problème technique momentané. "
            "Veuillez réessayer dans quelques instants."
        )


# ============================================================
# RAPPORT PAR DÉFAUT (en cas d'erreur)
# ============================================================

def _default_report() -> dict:
    """
    Rapport de secours retourné quand l'IA est indisponible.
    Permet à l'application de continuer à fonctionner partiellement.
    """
    return {
        "health": {
            "status": "Analyse non disponible",
            "diseases": ["Analyse temporairement indisponible"],
            "treatments": ["Veuillez réessayer ultérieurement"]
        },
        "edibility": {
            "verdict": "non",
            "edible_parts": ["Information non disponible"],
            "recipes": ["Information non disponible"],
            "warnings": ["Par précaution, ne pas consommer sans identification certaine"]
        },
        "medicinal": {
            "uses": ["Information non disponible"],
            "dosage": "Consulter un professionnel de santé",
            "contraindications": ["Consulter un professionnel de santé"]
        },
        "toxicity": {
            "level": "inconnu",
            "symptoms": ["Information non disponible"],
            "first_aid": "En cas de doute, contacter immédiatement un médecin"
        },
        "environment": {
            "invasive": False,
            "allelopathic": False,
            "soil_impact": "Information non disponible",
            "agricultural_impact": "Information non disponible"
        }
    }
