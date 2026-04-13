// ============================================================
// FICHIER : frontend/js/auth.js
// RÔLE    : Gestion de l'authentification côté frontend
//           (connexion, inscription, déconnexion, protection des pages)
// ============================================================


// ============================================================
// FONCTIONS DE NAVIGATION ENTRE LES ONGLETS (index.html)
// ============================================================

/**
 * Afficher l'onglet "login", "register" ou "forgot".
 * @param {string} tab - "login", "register" ou "forgot"
 */
function showTab(tab) {
    const loginForm    = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const forgotForm   = document.getElementById("forgotForm");
    const loginTab     = document.getElementById("loginTab");
    const registerTab  = document.getElementById("registerTab");

    // Cacher tous les formulaires
    loginForm?.classList.add("d-none");
    registerForm?.classList.add("d-none");
    forgotForm?.classList.add("d-none");

    // Désactiver tous les onglets
    loginTab?.classList.remove("active");
    registerTab?.classList.remove("active");

    if (tab === "login") {
        loginForm?.classList.remove("d-none");
        loginTab?.classList.add("active");
    } else if (tab === "register") {
        registerForm?.classList.remove("d-none");
        registerTab?.classList.add("active");
    } else if (tab === "forgot") {
        // Le formulaire "oublié" n'a pas d'onglet dédié dans la navbar
        forgotForm?.classList.remove("d-none");
    }
}


// ============================================================
// GESTION DES FORMULAIRES
// ============================================================

/**
 * Gérer la soumission du formulaire de connexion.
 * @param {Event} event - L'événement submit du formulaire
 */
async function handleLogin(event) {
    // Empêcher le comportement par défaut (rechargement de la page)
    event.preventDefault();

    // Récupérer les valeurs des champs
    const email    = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    // Afficher le spinner et désactiver le bouton
    setButtonLoading("loginBtn", "loginBtnText", "loginSpinner", true);
    hideAlert("loginAlert");

    try {
        // Appeler l'API de connexion
        const result = await apiPost("/api/auth/login", { email, password });

        // Sauvegarder le token JWT dans le localStorage
        // localStorage = stockage persistant dans le navigateur
        localStorage.setItem("access_token", result.access_token);

        // Rediriger vers le tableau de bord
        window.location.href = "/dashboard";

    } catch (error) {
        // Afficher le message d'erreur
        showAlert("loginAlert", error.message, "danger");
        setButtonLoading("loginBtn", "loginBtnText", "loginSpinner", false);
    }
}


/**
 * Gérer la soumission du formulaire d'inscription.
 * @param {Event} event - L'événement submit du formulaire
 */
async function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById("registerUsername").value.trim();
    const email    = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;

    // Validation basique côté client avant d'envoyer à l'API
    if (password.length < 6) {
        showAlert("registerAlert", "Le mot de passe doit contenir au moins 6 caractères.", "warning");
        return;
    }

    setButtonLoading("registerBtn", "registerBtnText", "registerSpinner", true);
    hideAlert("registerAlert");

    try {
        // Créer le compte
        await apiPost("/api/auth/register", { username, email, password });

        // Afficher un message de succès avec instruction de vérification email
        showAlert("registerAlert",
            "Compte créé ! Un email de vérification a été envoyé à " + email + ". " +
            "Cliquez sur le lien dans l'email pour activer votre compte.",
            "success"
        );

        // Passer automatiquement à l'onglet de connexion après 3s
        setTimeout(() => {
            showTab("login");
            document.getElementById("loginEmail").value = email;
        }, 3000);

    } catch (error) {
        showAlert("registerAlert", error.message, "danger");
    } finally {
        // "finally" = toujours exécuté, même en cas d'erreur
        setButtonLoading("registerBtn", "registerBtnText", "registerSpinner", false);
    }
}


/**
 * Gérer la soumission du formulaire "Mot de passe oublié".
 * Envoie l'email à l'API qui enverra le lien de réinitialisation.
 * @param {Event} event
 */
async function handleForgotPassword(event) {
    event.preventDefault();

    const email = document.getElementById("forgotEmail").value.trim();

    setButtonLoading("forgotBtn", "forgotBtnText", "forgotSpinner", true);
    hideAlert("forgotAlert");

    try {
        const result = await apiPost("/api/auth/forgot-password", { email });

        // Afficher le message de succès (même si l'email n'existe pas, pour la sécurité)
        showAlert("forgotAlert",
            result.message || "Si cet email est enregistré, vous recevrez un lien de réinitialisation.",
            "success"
        );

        // Vider le champ email
        document.getElementById("forgotEmail").value = "";

    } catch (error) {
        showAlert("forgotAlert", error.message, "danger");
    } finally {
        setButtonLoading("forgotBtn", "forgotBtnText", "forgotSpinner", false);
    }
}


// ============================================================
// DÉCONNEXION
// ============================================================

/**
 * Déconnecter l'utilisateur.
 * Supprime le token du localStorage et redirige vers la page de login.
 */
function logout() {
    // Supprimer le token → l'utilisateur ne sera plus authentifié
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_data");

    // Rediriger vers la page de connexion
    window.location.href = "/login";
}


// ============================================================
// PROTECTION DES PAGES (routes privées)
// ============================================================

/**
 * Vérifier que l'utilisateur est connecté.
 * Si ce n'est pas le cas, rediriger vers la page de login.
 *
 * À appeler en haut de chaque page protégée :
 *   document.addEventListener("DOMContentLoaded", () => { requireAuth(); });
 */
function requireAuth() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        // Pas de token = pas connecté → redirection login
        window.location.href = "/login";
        return false;
    }

    // Vérifier si le token est expiré (décodage simple du JWT)
    try {
        // JWT utilise base64URL (- et _ au lieu de + et /)
        // atob() nécessite du base64 standard + padding avec "="
        const raw = token.split(".")[1]
            .replace(/-/g, "+")
            .replace(/_/g, "/");
        // Ajouter le padding manquant (multiple de 4 requis)
        const padded = raw + "=".repeat((4 - raw.length % 4) % 4);
        const payload = JSON.parse(atob(padded));
        const now = Math.floor(Date.now() / 1000);

        if (payload.exp && payload.exp < now) {
            // Token expiré → déconnexion
            logout();
            return false;
        }
    } catch (e) {
        // Ne pas déconnecter sur une erreur de décodage —
        // laisser l'API décider si le token est valide
        console.warn("requireAuth: impossible de décoder le token localement, on laisse passer.");
    }

    return true;
}

/**
 * Rediriger vers le dashboard si déjà connecté.
 * À appeler sur la page de login pour éviter d'y rester si déjà connecté.
 */
function redirectIfAuthenticated() {
    const token = localStorage.getItem("access_token");
    if (token) {
        window.location.href = "/dashboard";
    }
}


// ============================================================
// UTILITAIRES UI POUR LES FORMULAIRES
// ============================================================

/**
 * Afficher/masquer un message d'alerte dans un formulaire.
 *
 * @param {string} alertId - L'ID de l'élément alert
 * @param {string} message - Le message à afficher
 * @param {string} type    - "success", "danger", "warning", "info"
 */
function showAlert(alertId, message, type) {
    const alert = document.getElementById(alertId);
    if (!alert) return;

    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="bi bi-${type === 'danger' ? 'exclamation-circle' : 'check-circle'} me-2"></i>${message}`;
    alert.classList.remove("d-none");
}

/**
 * Cacher un message d'alerte.
 * @param {string} alertId - L'ID de l'élément alert
 */
function hideAlert(alertId) {
    const alert = document.getElementById(alertId);
    if (alert) alert.classList.add("d-none");
}

/**
 * Activer/désactiver l'état de chargement d'un bouton.
 *
 * @param {string} btnId      - ID du bouton
 * @param {string} textId     - ID du span contenant le texte normal
 * @param {string} spinnerId  - ID du span contenant le spinner
 * @param {boolean} isLoading - true = afficher spinner, false = texte normal
 */
function setButtonLoading(btnId, textId, spinnerId, isLoading) {
    const btn     = document.getElementById(btnId);
    const text    = document.getElementById(textId);
    const spinner = document.getElementById(spinnerId);

    if (!btn) return;

    btn.disabled = isLoading;
    if (text)    text.classList.toggle("d-none", isLoading);
    if (spinner) spinner.classList.toggle("d-none", !isLoading);
}

/**
 * Afficher/masquer le mot de passe dans un champ input.
 *
 * @param {string} inputId - L'ID du champ mot de passe
 */
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const eye   = document.getElementById(inputId + "Eye");

    if (input.type === "password") {
        input.type = "text";
        if (eye) { eye.classList.remove("bi-eye"); eye.classList.add("bi-eye-slash"); }
    } else {
        input.type = "password";
        if (eye) { eye.classList.remove("bi-eye-slash"); eye.classList.add("bi-eye"); }
    }
}


/**
 * Charger le nom d'utilisateur dans la navbar.
 * À appeler sur toutes les pages protégées.
 */
async function loadNavUser() {
    try {
        const user = await apiGet("/api/auth/me");
        const el = document.getElementById("navUsername");
        if (el) el.textContent = user.username;
    } catch (e) {
        // Silencieux — la redirection vers login est gérée par requireAuth()
    }
}


// ============================================================
// AUTO-EXÉCUTION : Vérifier l'état de connexion au chargement
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;

    // Sur la page de login : rediriger si déjà connecté
    if (currentPath === "/login" || currentPath === "/index.html") {
        redirectIfAuthenticated();
    }

    // Récupérer le token Google OAuth depuis l'URL (?token=xxx)
    // Google redirige vers /dashboard?token=xxx après connexion
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get("token");
    if (tokenFromUrl) {
        localStorage.setItem("access_token", tokenFromUrl);
        // Nettoyer l'URL (supprimer le token visible dans la barre d'adresse)
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Afficher une erreur Google si présente dans l'URL
    const googleError = urlParams.get("error");
    if (googleError) {
        const alertEl = document.getElementById("loginAlert");
        if (alertEl) {
            alertEl.className = "alert alert-danger";
            alertEl.innerHTML = `<i class="bi bi-exclamation-circle me-2"></i>
                La connexion avec Google a échoué. Réessayez ou utilisez email/mot de passe.`;
            alertEl.classList.remove("d-none");
        }
    }
});
