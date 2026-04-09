// ============================================================
// FICHIER : frontend/js/chat.js
// RÔLE    : Gestion du chat avec l'agent IA sur rapport.html
// ============================================================

// ID du scan courant (récupéré depuis l'URL)
let currentScanId = null;

// ============================================================
// INITIALISATION DU CHAT
// ============================================================

/**
 * Charger l'historique de conversation d'un scan.
 * Appelée depuis rapport.js après le chargement du rapport.
 * @param {string|number} scanId
 */
async function loadChatHistory(scanId) {
    currentScanId = scanId;
    try {
        const messages = await apiGet(`/api/chat/${scanId}/history`);

        // S'il y a des messages existants, les afficher (en plus du message d'accueil)
        if (messages && messages.length > 0) {
            // Vider le message d'accueil par défaut
            const chatWindow = document.getElementById("chatWindow");
            chatWindow.innerHTML = "";

            // Afficher chaque message de l'historique
            messages.forEach(msg => appendMessage(msg.role, msg.content, false));
        }
    } catch (error) {
        // Silencieux : l'historique vide n'est pas une erreur critique
        console.log("Pas d'historique de chat pour ce scan.");
    }
}


// ============================================================
// ENVOI DE MESSAGES
// ============================================================

/**
 * Envoyer le message saisi par l'utilisateur.
 * Appelée par le bouton "Envoyer" ou la touche Entrée.
 */
async function sendChatMessage() {
    const input   = document.getElementById("chatInput");
    const message = input.value.trim();

    // Ne rien faire si le champ est vide
    if (!message) return;
    if (!currentScanId) {
        showToast("Aucun scan sélectionné pour le chat.", "warning");
        return;
    }

    // Vider le champ de saisie
    input.value = "";

    // Afficher le message de l'utilisateur immédiatement (sans attendre l'API)
    appendMessage("user", message, true);

    // Afficher l'indicateur "en train d'écrire..."
    showTypingIndicator();

    // Désactiver le bouton pendant l'envoi
    setButtonLoading("chatSendBtn", "chatBtnText", "chatBtnSpinner", true);
    input.disabled = true;

    try {
        // Appeler l'API de chat
        const result = await apiPost(`/api/chat/${currentScanId}`, { message });

        // Supprimer l'indicateur de frappe
        removeTypingIndicator();

        // Afficher la réponse de l'IA
        appendMessage("assistant", result.response, true);

    } catch (error) {
        removeTypingIndicator();
        appendMessage("assistant",
            "Désolé, je rencontre un problème technique. Veuillez réessayer.",
            true
        );
    } finally {
        // Réactiver le bouton et l'input
        setButtonLoading("chatSendBtn", "chatBtnText", "chatBtnSpinner", false);
        input.disabled = false;
        input.focus();
    }
}


/**
 * Envoyer une question rapide prédéfinie.
 * Appelée par les boutons de suggestions.
 * @param {HTMLElement} btn - Le bouton cliqué
 */
function sendQuickQuestion(btn) {
    const question = btn.textContent.trim();
    document.getElementById("chatInput").value = question;
    sendChatMessage();
}


// ============================================================
// AFFICHAGE DES MESSAGES
// ============================================================

/**
 * Ajouter un message dans la fenêtre de chat.
 *
 * @param {string} role    - "user" ou "assistant"
 * @param {string} content - Le texte du message
 * @param {boolean} scroll - Faire défiler vers le bas après l'ajout
 */
function appendMessage(role, content, scroll = true) {
    const chatWindow = document.getElementById("chatWindow");

    // Créer l'élément du message
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${role === "user" ? "user-message" : "assistant-message"}`;

    // Formater le contenu (convertir les sauts de ligne en <br>)
    const formattedContent = content.replace(/\n/g, "<br>");

    messageDiv.innerHTML = `
        <div class="message-bubble">${formattedContent}</div>
        <small class="text-muted mt-1">
            ${role === "user" ? "Vous" : '<i class="bi bi-robot me-1 text-success"></i>Agent IA'}
        </small>
    `;

    chatWindow.appendChild(messageDiv);

    // Faire défiler vers le bas pour voir le nouveau message
    if (scroll) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}


/**
 * Afficher l'indicateur "en train d'écrire..." (3 points animés).
 */
function showTypingIndicator() {
    const chatWindow = document.getElementById("chatWindow");

    const indicator = document.createElement("div");
    indicator.className = "chat-message assistant-message";
    indicator.id = "typingIndicator";

    indicator.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <small class="text-muted mt-1">
            <i class="bi bi-robot me-1 text-success"></i>Agent IA écrit...
        </small>
    `;

    chatWindow.appendChild(indicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}


/**
 * Supprimer l'indicateur "en train d'écrire...".
 */
function removeTypingIndicator() {
    const indicator = document.getElementById("typingIndicator");
    if (indicator) indicator.remove();
}
