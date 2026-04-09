# ============================================================
# FICHIER : backend/routers/chat.py
# RÔLE    : Endpoints pour l'agent conversationnel IA
#
# CONCEPT POUR DÉBUTANT :
#   L'agent conversationnel permet à l'utilisateur de poser
#   des questions sur la plante qu'il vient d'analyser.
#   L'IA (Groq) connaît le contexte du scan et peut répondre
#   de manière précise et personnalisée.
# ============================================================

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Scan, ChatMessage, User
from schemas import ChatMessageCreate, ChatMessageResponse, ChatResponse
from routers.auth import get_current_user
from services import groq_ai
from services.plant_lookup import find_local_plant, build_local_context_block

router = APIRouter()


@router.post("/{scan_id}", response_model=ChatResponse)
async def send_message(
    scan_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Envoyer un message à l'agent IA et recevoir une réponse.

    PARAMÈTRE URL :
        scan_id : L'ID du scan sur lequel porte la conversation

    CORPS DE LA REQUÊTE :
        { "message": "Comment préparer une décoction avec cette plante ?" }

    ÉTAPES :
    1. Vérifier que le scan appartient à l'utilisateur
    2. Récupérer l'historique de la conversation
    3. Construire le contexte de la plante
    4. Appeler Groq avec tout le contexte
    5. Sauvegarder les deux messages (question + réponse)
    6. Retourner la réponse
    """

    # Étape 1 : Vérifier l'accès au scan
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.user_id == current_user.id
    ).first()

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan non trouvé ou accès non autorisé."
        )

    # Étape 2 : Récupérer l'historique des messages
    # On limite à 10 messages pour ne pas surcharger l'IA
    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.scan_id == scan_id
    ).order_by(ChatMessage.created_at.asc()).limit(20).all()

    # Convertir les messages en format attendu par Groq
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in previous_messages
    ]

    # Étape 3 : Construire le contexte de la plante
    plant_context = {
        "plant_name": scan.plant_name,
        "scientific_name": scan.plant_scientific_name,
        "family": scan.plant_family,
        "confidence_score": scan.confidence_score,
        "report": json.loads(scan.report_json) if scan.report_json else {}
    }

    # Étape 3.5 : Enrichir avec les données de notre catalogue local
    # L'agent conversationnel connaît ainsi les usages locaux ivoiriens,
    # les noms en dioula/baoulé, les régions de présence en CI, etc.
    local_data    = find_local_plant(db, {
        "plant_name":     scan.plant_name,
        "scientific_name": scan.plant_scientific_name,
        "family":         scan.plant_family,
    })
    local_context = build_local_context_block(local_data) if local_data else ""

    # Étape 4 : Obtenir la réponse de l'IA (avec contexte local enrichi)
    ai_response = await groq_ai.chat_with_agent(
        plant_context=plant_context,
        conversation_history=conversation_history,
        user_message=message_data.message,
        local_context=local_context
    )

    # Étape 5 : Sauvegarder le message de l'utilisateur
    user_message_record = ChatMessage(
        scan_id=scan_id,
        role="user",
        content=message_data.message
    )
    db.add(user_message_record)

    # Sauvegarder la réponse de l'IA
    ai_message_record = ChatMessage(
        scan_id=scan_id,
        role="assistant",
        content=ai_response
    )
    db.add(ai_message_record)
    db.commit()
    db.refresh(ai_message_record)

    # Étape 6 : Retourner la réponse
    return ChatResponse(
        response=ai_response,
        message_id=ai_message_record.id
    )


@router.get("/{scan_id}/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer l'historique complet de la conversation pour un scan.
    Utile pour recharger la page et retrouver la conversation précédente.
    """
    # Vérifier l'accès au scan
    scan = db.query(Scan).filter(
        Scan.id == scan_id,
        Scan.user_id == current_user.id
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan non trouvé.")

    # Récupérer tous les messages triés chronologiquement
    messages = db.query(ChatMessage).filter(
        ChatMessage.scan_id == scan_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return messages
