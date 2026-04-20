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
    event.preventDefault();

    const email    = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    setButtonLoading("loginBtn", "loginBtnText", "loginSpinner", true);
    hideAlert("loginAlert");

    try {
        const result = await apiPost("/api/auth/login", { email, password });
        localStorage.setItem("access_token", result.access_token);
        window.location.href = "/dashboard";

    } catch (error) {
        const msg = error.message || "";

        if (msg.includes("Aucun compte")) {
            // Email inconnu → proposer de créer un compte
            showLoginSmartAlert(
                "bi-person-x",
                "Aucun compte trouvé avec cet email.",
                "Vous n'avez pas encore de compte ?",
                "Créer un compte gratuit",
                () => { showTab("register"); prefillRegisterEmail(email); }
            );

        } else if (msg.includes("Mot de passe incorrect")) {
            // Mauvais mot de passe → proposer la réinitialisation
            showLoginSmartAlert(
                "bi-lock-fill",
                "Mot de passe incorrect.",
                "Vous avez oublié votre mot de passe ?",
                "Réinitialiser le mot de passe",
                () => { showTab("forgot"); prefillForgotEmail(email); },
                "warning"
            );

        } else if (msg.includes("Google")) {
            // Compte Google → afficher bouton Google
            showLoginSmartAlert(
                "bi-google",
                "Ce compte utilise la connexion Google.",
                "Utilisez le bouton ci-dessous pour vous connecter.",
                "Continuer avec Google",
                () => { window.location.href = "/api/auth/google/login"; },
                "info"
            );

        } else if (msg.includes("non vérifié")) {
            // Email non confirmé
            showLoginSmartAlert(
                "bi-envelope-exclamation",
                "Compte non vérifié.",
                "Vérifiez votre boîte email et cliquez sur le lien d'activation.",
                "Renvoyer l'email de vérification",
                () => resendVerification(email),
                "warning"
            );

        } else {
            showAlert("loginAlert", msg, "danger");
        }

        setButtonLoading("loginBtn", "loginBtnText", "loginSpinner", false);
    }
}


/**
 * Afficher une alerte enrichie avec titre, message et bouton d'action.
 */
function showLoginSmartAlert(icon, title, subtitle, btnLabel, btnAction, type = "danger") {
    const el = document.getElementById("loginAlert");
    if (!el) return;

    const colors = {
        danger:  { bg: "#fee2e2", color: "#dc2626", border: "#dc2626", btnBg: "#dc2626" },
        warning: { bg: "#fef3c7", color: "#d97706", border: "#d97706", btnBg: "#d97706" },
        info:    { bg: "#dbeafe", color: "#2563eb", border: "#2563eb", btnBg: "#2563eb" },
    };
    const c = colors[type] || colors.danger;

    el.style.cssText = `
        background:${c.bg}; color:${c.color};
        border-left:3px solid ${c.border};
        padding:12px 14px; border-radius:10px;
        font-size:0.85rem; margin-bottom:1rem;
    `;
    el.innerHTML = `
        <div class="d-flex align-items-start gap-2">
            <i class="bi ${icon} mt-1" style="font-size:1rem;flex-shrink:0;"></i>
            <div style="flex:1;">
                <div style="font-weight:700;">${title}</div>
                <div style="opacity:0.85;font-size:0.8rem;margin-top:2px;">${subtitle}</div>
                <button onclick="(${btnAction.toString()})()"
                    style="margin-top:8px;background:${c.btnBg};color:#fff;border:none;
                           border-radius:8px;padding:6px 14px;font-size:0.8rem;
                           font-weight:600;cursor:pointer;width:100%;">
                    ${btnLabel}
                </button>
            </div>
        </div>
    `;
    el.style.display = "block";
}


/** Pré-remplir l'email dans le formulaire d'inscription. */
function prefillRegisterEmail(email) {
    const el = document.getElementById("registerEmail");
    if (el) el.value = email;
}

/** Pré-remplir l'email dans le formulaire de connexion. */
function prefillLoginEmail(email) {
    const el = document.getElementById("loginEmail");
    if (el) el.value = email;
}

/** Pré-remplir l'email dans le formulaire "mot de passe oublié". */
function prefillForgotEmail(email) {
    const el = document.getElementById("forgotEmail");
    if (el) el.value = email;
}

/** Renvoyer l'email de vérification. */
async function resendVerification(email) {
    try {
        await apiPost("/api/auth/resend-verification", { email });
        showAlert("loginAlert", "Email de vérification renvoyé ! Vérifiez votre boîte mail.", "success");
    } catch (e) {
        showAlert("loginAlert", e.message, "danger");
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
        await apiPost("/api/auth/register", { username, email, password });

        // Succès : message clair + redirection auto vers login
        const alertEl = document.getElementById("registerAlert");
        alertEl.style.cssText = `
            background:#d1fae5; color:#059669; border-left:3px solid #059669;
            padding:12px 14px; border-radius:10px; font-size:0.85rem; margin-bottom:1rem;
        `;
        alertEl.innerHTML = `
            <div class="d-flex align-items-start gap-2">
                <i class="bi bi-check-circle-fill mt-1" style="font-size:1rem;flex-shrink:0;"></i>
                <div>
                    <div style="font-weight:700;">Compte créé avec succès ! 🎉</div>
                    <div style="opacity:0.85;font-size:0.8rem;margin-top:2px;">
                        Un email de vérification a été envoyé à <strong>${email}</strong>.<br>
                        Cliquez sur le lien dans l'email pour activer votre compte.
                    </div>
                </div>
            </div>
        `;
        alertEl.style.display = "block";

        setTimeout(() => {
            showTab("login");
            document.getElementById("loginEmail").value = email;
        }, 3000);

    } catch (error) {
        const msg = error.message || "";

        if (msg.includes("email existe déjà") || msg.includes("email")) {
            // Email déjà utilisé → proposer de se connecter
            const alertEl = document.getElementById("registerAlert");
            alertEl.style.cssText = `
                background:#fef3c7; color:#d97706; border-left:3px solid #d97706;
                padding:12px 14px; border-radius:10px; font-size:0.85rem; margin-bottom:1rem;
            `;
            alertEl.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <i class="bi bi-person-check mt-1" style="font-size:1rem;flex-shrink:0;"></i>
                    <div style="flex:1;">
                        <div style="font-weight:700;">Un compte existe déjà avec cet email.</div>
                        <div style="opacity:0.85;font-size:0.8rem;margin-top:2px;">Vous avez déjà un compte ? Connectez-vous directement.</div>
                        <button onclick="showTab('login'); prefillLoginEmail('${email}')"
                            style="margin-top:8px;background:#d97706;color:#fff;border:none;
                                   border-radius:8px;padding:6px 14px;font-size:0.8rem;
                                   font-weight:600;cursor:pointer;width:100%;">
                            Se connecter
                        </button>
                    </div>
                </div>
            `;
            alertEl.style.display = "block";
        } else {
            showAlert("registerAlert", msg, "danger");
        }
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

    // -------------------------------------------------------
    // Récupérer le token Google OAuth (cookie ou URL param)
    // Le backend pose un cookie court "google_token" après OAuth
    // On le transfère dans localStorage puis on supprime le cookie
    // -------------------------------------------------------
    function readCookie(name) {
        const match = document.cookie.split("; ").find(r => r.startsWith(name + "="));
        return match ? match.split("=")[1] : null;
    }

    const cookieToken = readCookie("google_token");
    if (cookieToken) {
        localStorage.setItem("access_token", cookieToken);
        // Supprimer le cookie immédiatement
        document.cookie = "google_token=; Max-Age=0; path=/";
    }

    // Fallback : token dans l'URL (ancienne méthode, gardée pour compatibilité)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get("token");
    if (tokenFromUrl && !cookieToken) {
        localStorage.setItem("access_token", tokenFromUrl);
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
