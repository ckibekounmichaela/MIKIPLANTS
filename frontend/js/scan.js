// ============================================================
// FICHIER : frontend/js/scan.js
// RÔLE    : Gestion de la page d'analyse (scan.html)
//           - Onglet 1 : Caméra en temps réel (getUserMedia)
//           - Onglet 2 : Upload d'image (drag & drop)
//           - Envoi à l'API et suivi de progression
// ============================================================

// ============================================================
// VARIABLES GLOBALES
// ============================================================

// Fichier image sélectionné (upload ou capture caméra)
let selectedFile   = null;

// Coordonnées GPS (si l'utilisateur active la géolocalisation)
let userLatitude   = null;
let userLongitude  = null;

// Onglet actif : "camera" ou "upload"
let activeScanTab  = "camera";

// --- Variables caméra ---
let cameraStream   = null;   // Flux vidéo actif (MediaStream)
let facingMode     = "environment";  // "environment" = caméra arrière, "user" = caméra frontale


// ============================================================
// INITIALISATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    if (!requireAuth()) return;
    loadNavUser();

    // Cacher la vidéo et afficher le bouton "Démarrer la caméra" au début
    document.getElementById("videoSection").classList.add("d-none");
    document.getElementById("startCameraSection").classList.remove("d-none");
    document.getElementById("capturedSection").classList.add("d-none");

    // Demander la géolocalisation automatiquement et silencieusement
    requestGeolocation();
});


// ============================================================
// NAVIGATION ENTRE LES ONGLETS (Caméra / Upload)
// ============================================================

/**
 * Basculer entre l'onglet caméra et l'onglet upload.
 * @param {string} tab - "camera" ou "upload"
 */
function switchScanTab(tab) {
    activeScanTab = tab;

    const cameraTab   = document.getElementById("cameraTab");
    const uploadTab   = document.getElementById("uploadTab");
    const tabCameraBtn = document.getElementById("tabCameraBtn");
    const tabUploadBtn = document.getElementById("tabUploadBtn");

    if (tab === "camera") {
        cameraTab.classList.remove("d-none");
        uploadTab.classList.add("d-none");
        tabCameraBtn.classList.add("active");
        tabUploadBtn.classList.remove("active");
    } else {
        uploadTab.classList.remove("d-none");
        cameraTab.classList.add("d-none");
        tabUploadBtn.classList.add("active");
        tabCameraBtn.classList.remove("active");

        // Arrêter la caméra si elle tourne quand on quitte l'onglet
        if (cameraStream) stopCamera();
    }

    // Réinitialiser les erreurs et la progression
    document.getElementById("errorAlert").classList.add("d-none");
    document.getElementById("progressSection").classList.add("d-none");
}


// ============================================================
// ONGLET 1 : CAMÉRA EN TEMPS RÉEL
// ============================================================

/**
 * Démarrer la caméra via l'API getUserMedia du navigateur.
 *
 * CONCEPT :
 *   navigator.mediaDevices.getUserMedia() demande l'accès à la caméra.
 *   Le navigateur affiche une popup de permission à l'utilisateur.
 *   Si accepté, on reçoit un "MediaStream" qu'on connecte à l'élément <video>.
 */
async function startCamera() {
    try {
        // Demander l'accès à la caméra
        // facingMode: "environment" = caméra arrière (idéal pour les plantes en extérieur)
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: facingMode,
                width:  { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        // Connecter le flux vidéo à l'élément <video>
        const video = document.getElementById("cameraPreview");
        video.srcObject = cameraStream;

        // Afficher la vidéo, cacher le bouton de démarrage
        document.getElementById("startCameraSection").classList.add("d-none");
        document.getElementById("videoSection").classList.remove("d-none");
        document.getElementById("capturedSection").classList.add("d-none");

    } catch (err) {
        // Gérer les différents types d'erreurs de permission
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            showScanError("Accès à la caméra refusé. Autorisez l'accès dans les paramètres de votre navigateur.");
        } else if (err.name === "NotFoundError") {
            showScanError("Aucune caméra détectée sur cet appareil.");
        } else {
            showScanError("Impossible d'accéder à la caméra : " + err.message);
        }
    }
}


/**
 * Arrêter la caméra et libérer les ressources.
 *
 * IMPORTANT : Toujours arrêter le flux quand on n'en a plus besoin,
 * sinon le voyant de caméra reste allumé sur l'appareil.
 */
function stopCamera() {
    if (cameraStream) {
        // Arrêter chaque piste du flux (vidéo, audio...)
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }

    const video = document.getElementById("cameraPreview");
    video.srcObject = null;

    // Revenir à l'écran de démarrage
    document.getElementById("videoSection").classList.add("d-none");
    document.getElementById("capturedSection").classList.add("d-none");
    document.getElementById("startCameraSection").classList.remove("d-none");
}


/**
 * Basculer entre caméra avant et caméra arrière.
 * Utile sur mobile pour passer de la caméra selfie à la caméra principale.
 */
async function switchCamera() {
    // Inverser la caméra
    facingMode = facingMode === "environment" ? "user" : "environment";

    // Arrêter la caméra actuelle et en démarrer une nouvelle
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }

    await startCamera();
}


/**
 * Capturer une photo depuis le flux vidéo en direct.
 *
 * CONCEPT :
 *   On dessine l'image courante du <video> sur un <canvas> invisible,
 *   puis on convertit ce canvas en un objet File utilisable comme un upload.
 */
function capturePhoto() {
    const video  = document.getElementById("cameraPreview");
    const canvas = document.getElementById("cameraCanvas");

    // Définir la taille du canvas = taille de la vidéo
    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 720;

    // Dessiner l'image courante de la vidéo sur le canvas
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convertir le canvas en Blob (données binaires de l'image)
    // "image/jpeg" avec qualité 0.92 = bon rapport qualité/taille
    canvas.toBlob((blob) => {
        if (!blob) {
            showScanError("Impossible de capturer la photo. Réessayez.");
            return;
        }

        // Créer un objet File depuis le Blob (comme si l'utilisateur avait uploadé un fichier)
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        selectedFile = new File([blob], `capture_${timestamp}.jpg`, { type: "image/jpeg" });

        // Afficher la photo capturée
        const capturedImg = document.getElementById("capturedPhoto");
        capturedImg.src   = canvas.toDataURL("image/jpeg", 0.92);

        // Arrêter la vidéo et afficher la section de capture
        stopCamera();
        document.getElementById("startCameraSection").classList.add("d-none");
        document.getElementById("videoSection").classList.add("d-none");
        document.getElementById("capturedSection").classList.remove("d-none");

    }, "image/jpeg", 0.92);
}


/**
 * Reprendre une photo : relancer la caméra.
 */
function retakePhoto() {
    selectedFile = null;
    document.getElementById("capturedSection").classList.add("d-none");
    startCamera();
}


// ============================================================
// ONGLET 2 : UPLOAD D'IMAGE
// ============================================================

/**
 * Gérer la sélection d'un fichier via l'input file standard.
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) processFile(file);
}

/**
 * Gérer le survol drag & drop.
 */
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById("uploadZone").classList.add("drag-over");
}

/**
 * Gérer la sortie de la zone drag & drop.
 */
function handleDragLeave(event) {
    event.preventDefault();
    document.getElementById("uploadZone").classList.remove("drag-over");
}

/**
 * Gérer le dépôt d'un fichier par drag & drop.
 */
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    document.getElementById("uploadZone").classList.remove("drag-over");
    const file = event.dataTransfer.files[0];
    if (file) processFile(file);
}

/**
 * Valider et prévisualiser un fichier image sélectionné (upload).
 * @param {File} file
 */
function processFile(file) {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
        showToast("Type de fichier non supporté. Utilisez JPG, PNG ou WebP.", "danger");
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showToast("L'image est trop volumineuse. Maximum 5 MB.", "warning");
        return;
    }

    selectedFile = file;

    // Afficher la prévisualisation
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById("previewImg").src = e.target.result;
        document.getElementById("previewFileName").textContent =
            `${file.name} (${(file.size / 1024).toFixed(0)} Ko)`;
        document.getElementById("uploadPlaceholder").classList.add("d-none");
        document.getElementById("imagePreview").classList.remove("d-none");
    };
    reader.readAsDataURL(file);

    // Activer le bouton Analyser
    document.getElementById("analyzeBtn").disabled = false;
}

/**
 * Supprimer l'image sélectionnée et réinitialiser la zone d'upload.
 */
function clearImage(event) {
    event.stopPropagation();
    selectedFile = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("imagePreview").classList.add("d-none");
    document.getElementById("uploadPlaceholder").classList.remove("d-none");
    document.getElementById("analyzeBtn").disabled = true;
}


// ============================================================
// GÉOLOCALISATION
// ============================================================

// Promise GPS globale — résolue dès que la position est connue (ou refusée)
let geoPromise = null;

/**
 * Demande le GPS et stocke une Promise qui se résout quand la position est connue.
 * Appelée au chargement de la page → position prête quand l'utilisateur lance l'analyse.
 */
function requestGeolocation() {
    if (!navigator.geolocation) {
        geoPromise = Promise.resolve(null);
        setGeoStatus("unavailable");
        return;
    }

    geoPromise = new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                userLatitude  = pos.coords.latitude;
                userLongitude = pos.coords.longitude;
                const latEl = document.getElementById("latitude");
                const lngEl = document.getElementById("longitude");
                if (latEl) latEl.value = userLatitude;
                if (lngEl) lngEl.value = userLongitude;
                setGeoStatus("ok");
                resolve({ lat: userLatitude, lng: userLongitude });
            },
            () => {
                setGeoStatus("denied");
                resolve(null);  // Pas de position, mais on continue
            },
            { timeout: 8000, maximumAge: 60000 }
        );
    });
}

/**
 * Met à jour les indicateurs GPS visuels.
 */
function setGeoStatus(status) {
    const configs = {
        ok:          `<i class="bi bi-geo-alt-fill text-success me-1"></i><span class="text-success">📍 Position GPS obtenue</span>`,
        denied:      `<i class="bi bi-geo-alt text-muted me-1"></i><span class="text-muted">Position GPS refusée</span>`,
        unavailable: `<i class="bi bi-geo-alt text-muted me-1"></i><span class="text-muted">GPS non disponible</span>`,
        waiting:     `<i class="bi bi-geo-alt text-warning me-1"></i><span class="text-warning">Obtention du GPS...</span>`,
    };
    const html = configs[status] || configs.unavailable;
    const s1 = document.getElementById("geoStatus");
    const s2 = document.getElementById("geoStatusCamera");
    if (s1) s1.innerHTML = html;
    if (s2) s2.innerHTML = html;
}

/**
 * Ancienne fonction (conservée pour compatibilité).
 */
function toggleGeoloc(checkbox) {
    if (checkbox.checked) requestGeolocation();
    else { userLatitude = userLongitude = null; }
}


// ============================================================
// ENVOI DE L'ANALYSE (commun aux deux onglets)
// ============================================================

/**
 * Démarrer l'analyse de la plante.
 * Fonctionne que l'image vienne de la caméra ou d'un upload.
 */
async function startAnalysis() {
    if (!selectedFile) {
        showToast("Veuillez d'abord sélectionner ou capturer une image.", "warning");
        return;
    }

    // Afficher la progression et désactiver les boutons
    document.getElementById("progressSection").classList.remove("d-none");
    document.getElementById("errorAlert").classList.add("d-none");

    // Désactiver le bouton selon l'onglet actif
    if (activeScanTab === "upload") {
        setButtonLoading("analyzeBtn", "analyzeBtnText", "analyzeSpinner", true);
    } else {
        document.getElementById("analyzeCapturedBtn").disabled = true;
        document.getElementById("analyzeCapturedBtn").innerHTML =
            `<span class="spinner-border spinner-border-sm me-2"></span>Analyse en cours...`;
    }

    try {
        // Étape 1 : Identification PlantNet
        updateStep(1, "active", "Obtention de la position GPS...", 10);

        // Attendre que le GPS soit résolu (ou timeout) avant d'envoyer
        if (geoPromise) await geoPromise;

        updateStep(1, "active", "Envoi de l'image à PlantNet...", 30);
        await sleep(300);

        // Construire le FormData avec le fichier (upload ou capture)
        const formData = new FormData();
        formData.append("image", selectedFile);

        if (userLatitude)  formData.append("latitude",  userLatitude);
        if (userLongitude) formData.append("longitude", userLongitude);

        console.log("GPS envoyé :", userLatitude, userLongitude);

        updateStep(1, "active", "Identification en cours...", 70);

        // Étape 2 : Rapport IA
        updateStep(2, "active", "Génération du rapport par l'IA (Groq)...", 20);

        // Appel API unique qui fait tout (PlantNet + Groq + sauvegarde)
        const result = await apiPostFile("/api/scan/analyze", formData);

        updateStep(1, "done", "Plante identifiée ✓", 100);
        updateStep(2, "done", "Rapport généré ✓", 100);

        // Étape 3 : Finalisation
        updateStep(3, "active", "Sauvegarde du rapport...", 80);
        await sleep(300);
        updateStep(3, "done", "Analyse sauvegardée ✓", 100);

        // Rediriger vers la page de rapport
        await sleep(500);
        window.location.href = `/rapport?id=${result.id}`;

    } catch (error) {
        showScanError(error.message);

        // Réinitialiser les boutons
        if (activeScanTab === "upload") {
            setButtonLoading("analyzeBtn", "analyzeBtnText", "analyzeSpinner", false);
            document.getElementById("analyzeBtn").disabled = false;
        } else {
            document.getElementById("analyzeCapturedBtn").disabled = false;
            document.getElementById("analyzeCapturedBtn").innerHTML =
                `<i class="bi bi-search me-2"></i>Analyser cette photo`;
        }

        // Réinitialiser les étapes
        updateStep(1, "idle", "Envoi de l'image à PlantNet...", 0);
        updateStep(2, "idle", "En attente de l'identification...", 0);
        updateStep(3, "idle", "En attente...", 0);
        document.getElementById("progressSection").classList.add("d-none");
    }
}


// ============================================================
// MISE À JOUR DE L'INTERFACE DE PROGRESSION
// ============================================================

/**
 * Mettre à jour l'affichage d'une étape de progression.
 * @param {number} stepNum  - Numéro de l'étape (1, 2 ou 3)
 * @param {string} state    - "idle", "active" ou "done"
 * @param {string} text     - Texte descriptif
 * @param {number} progress - Largeur de la barre (0 à 100)
 */
function updateStep(stepNum, state, text, progress) {
    const step     = document.getElementById(`step${stepNum}`);
    const icon     = document.getElementById(`step${stepNum}Icon`);
    const bar      = document.getElementById(`step${stepNum}Bar`);
    const stepText = document.getElementById(`step${stepNum}Text`);

    if (!step) return;

    if (stepText) stepText.textContent = text;
    if (bar)      bar.style.width = `${progress}%`;

    if (state === "idle") {
        step.style.opacity = "0.4";
        if (icon) icon.innerHTML = `<i class="bi bi-hourglass text-muted"></i>`;
    } else if (state === "active") {
        step.style.opacity = "1";
        if (icon) icon.innerHTML = `<span class="spinner-border spinner-border-sm text-success"></span>`;
        if (bar)  bar.classList.add("progress-bar-striped", "progress-bar-animated");
    } else if (state === "done") {
        step.style.opacity = "1";
        if (icon) icon.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i>`;
        if (bar)  bar.classList.remove("progress-bar-striped", "progress-bar-animated");
    }
}


// ============================================================
// UTILITAIRES
// ============================================================

/** Afficher un message d'erreur sur la page. */
function showScanError(message) {
    const el = document.getElementById("errorAlert");
    document.getElementById("errorMessage").textContent = message;
    el.classList.remove("d-none");
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/** Attendre N millisecondes (pour les effets visuels). */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
