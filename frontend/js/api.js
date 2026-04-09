// ============================================================
// FICHIER : frontend/js/api.js
// RÔLE    : Fonctions utilitaires pour communiquer avec l'API
//
// CONCEPT POUR DÉBUTANT :
//   Ce fichier est une "boîte à outils" pour les appels API.
//   Au lieu de répéter le même code fetch() partout,
//   on centralise la logique ici et on réutilise ces fonctions.
//
//   fetch() est la fonction native du navigateur pour faire
//   des requêtes HTTP (GET, POST, DELETE...) vers un serveur.
// ============================================================

// URL de base de l'API (même serveur que le frontend)
const API_BASE = "";  // Vide = même domaine/port que la page HTML


// ============================================================
// FONCTIONS PRINCIPALES D'APPEL API
// ============================================================

/**
 * Faire une requête GET vers l'API.
 *
 * @param {string} endpoint - L'URL de l'endpoint (ex: "/api/auth/me")
 * @returns {Promise<any>} - Les données JSON retournées par l'API
 *
 * Exemple d'utilisation :
 *   const user = await apiGet("/api/auth/me");
 *   console.log(user.username);
 */
async function apiGet(endpoint) {
    // Récupérer le token JWT stocké dans localStorage
    const token = localStorage.getItem("access_token");

    const response = await fetch(API_BASE + endpoint, {
        method: "GET",
        headers: {
            // Toujours envoyer le token dans le header Authorization
            "Authorization": token ? `Bearer ${token}` : "",
            "Content-Type": "application/json"
        }
    });

    // Vérifier si la réponse est OK (code 200-299)
    await handleResponseErrors(response);

    // Convertir la réponse JSON en objet JavaScript
    return await response.json();
}


/**
 * Faire une requête POST vers l'API avec des données JSON.
 *
 * @param {string} endpoint - L'URL de l'endpoint
 * @param {object} data     - Les données à envoyer (seront converties en JSON)
 * @returns {Promise<any>}  - Les données JSON retournées par l'API
 *
 * Exemple d'utilisation :
 *   const token = await apiPost("/api/auth/login", {
 *     email: "user@test.com",
 *     password: "monmotdepasse"
 *   });
 */
async function apiPost(endpoint, data) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(API_BASE + endpoint, {
        method: "POST",
        headers: {
            "Authorization": token ? `Bearer ${token}` : "",
            "Content-Type": "application/json"
        },
        // JSON.stringify() convertit l'objet JS en texte JSON
        // Ex: {email: "a@b.com"} → '{"email":"a@b.com"}'
        body: JSON.stringify(data)
    });

    await handleResponseErrors(response);
    return await response.json();
}


/**
 * Faire une requête POST avec un fichier (multipart/form-data).
 * Utilisée pour envoyer des images à l'API.
 *
 * @param {string} endpoint   - L'URL de l'endpoint
 * @param {FormData} formData - Les données du formulaire (avec le fichier)
 * @returns {Promise<any>}
 *
 * Exemple d'utilisation :
 *   const formData = new FormData();
 *   formData.append("image", fileInput.files[0]);
 *   const result = await apiPostFile("/api/scan/analyze", formData);
 */
async function apiPostFile(endpoint, formData) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(API_BASE + endpoint, {
        method: "POST",
        headers: {
            // Ne PAS mettre "Content-Type" ici !
            // Le navigateur le définit automatiquement avec le boundary
            "Authorization": token ? `Bearer ${token}` : ""
        },
        body: formData
    });

    await handleResponseErrors(response);
    return await response.json();
}


/**
 * Faire une requête DELETE vers l'API.
 *
 * @param {string} endpoint - L'URL de l'endpoint (ex: "/api/scan/42")
 * @returns {Promise<void>}
 */
async function apiDelete(endpoint) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(API_BASE + endpoint, {
        method: "DELETE",
        headers: {
            "Authorization": token ? `Bearer ${token}` : ""
        }
    });

    // Pour DELETE, la réponse peut être vide (204 No Content)
    if (response.status === 204) return;
    await handleResponseErrors(response);
}


// ============================================================
// GESTION DES ERREURS
// ============================================================

/**
 * Vérifier si la réponse HTTP indique une erreur et la gérer.
 * Si le serveur retourne 401 (non autorisé), on redirige vers login.
 *
 * @param {Response} response - L'objet Response de fetch()
 */
async function handleResponseErrors(response) {
    if (response.ok) return;  // Tout va bien, pas d'erreur

    // 401 = Non autorisé → token expiré ou invalide → retour au login
    if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_data");
        window.location.href = "/login";
        return;
    }

    // Toute autre erreur → extraire le message d'erreur et le lancer
    let errorMessage = `Erreur ${response.status}`;
    try {
        const errorData = await response.json();
        // FastAPI retourne les erreurs dans le champ "detail"
        errorMessage = errorData.detail || errorMessage;
    } catch (e) {
        // Si la réponse n'est pas du JSON, utiliser le message par défaut
    }

    // "throw" crée une exception qui sera attrapée par les try/catch
    throw new Error(errorMessage);
}


// ============================================================
// FONCTIONS UTILITAIRES UI
// ============================================================

/**
 * Afficher une notification toast en bas à droite de l'écran.
 *
 * @param {string} message - Le message à afficher
 * @param {string} type    - "success", "danger", "warning", "info"
 * @param {number} duration - Durée d'affichage en ms (défaut: 4000)
 */
function showToast(message, type = "success", duration = 4000) {
    // Créer le conteneur s'il n'existe pas encore
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    // Icônes selon le type de toast
    const icons = {
        success: "bi-check-circle-fill",
        danger:  "bi-exclamation-circle-fill",
        warning: "bi-exclamation-triangle-fill",
        info:    "bi-info-circle-fill"
    };

    // Créer l'élément toast
    const toast = document.createElement("div");
    toast.className = `toast show align-items-center text-bg-${type} border-0 mb-2`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi ${icons[type] || "bi-info-circle-fill"} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                    onclick="this.closest('.toast').remove()"></button>
        </div>
    `;

    container.appendChild(toast);

    // Supprimer automatiquement après la durée spécifiée
    setTimeout(() => toast.remove(), duration);
}


/**
 * Formater une date ISO en format lisible français.
 * Ex: "2024-01-15T10:30:00" → "15/01/2024 à 10h30"
 *
 * @param {string} isoDate - Date au format ISO 8601
 * @returns {string} - Date formatée
 */
function formatDate(isoDate) {
    if (!isoDate) return "Date inconnue";
    const date = new Date(isoDate);
    return date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    }).replace(",", " à").replace(":", "h");
}


/**
 * Formater un score de confiance (0 à 1) en pourcentage.
 * Ex: 0.9456 → "94.6%"
 *
 * @param {number} score - Score entre 0 et 1
 * @returns {string}
 */
function formatConfidence(score) {
    return `${(score * 100).toFixed(1)}%`;
}
