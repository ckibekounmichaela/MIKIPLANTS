// ============================================================
// FICHIER : frontend/js/rapport.js
// RÔLE    : Affichage du rapport d'analyse sur rapport.html
//           Récupère le scan depuis l'API et remplit les 5 cards
// ============================================================

// Variable globale pour stocker les données du scan courant
let currentScan = null;

// ============================================================
// INITIALISATION
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
    // Vérifier l'authentification — stopper si pas connecté
    if (!requireAuth()) return;

    loadNavUser();

    // Récupérer l'ID du scan depuis l'URL
    // Ex: /rapport?id=42 → scanId = "42"
    const params = new URLSearchParams(window.location.search);
    const scanId = params.get("id");

    if (!scanId) {
        document.getElementById("loadingOverlay").classList.add("d-none");
        document.getElementById("errorOverlay").classList.remove("d-none");
        document.getElementById("errorOverlayMsg").textContent = "Aucun scan sélectionné.";
        return;
    }

    await loadRapport(scanId);
});


// ============================================================
// CHARGEMENT DU RAPPORT
// ============================================================

/**
 * Charger et afficher le rapport complet d'un scan.
 * @param {string|number} scanId - L'ID du scan à afficher
 */
async function loadRapport(scanId) {
    try {
        // Appeler l'API pour récupérer les données du scan
        const scan = await apiGet(`/api/scan/${scanId}`);
        currentScan = scan;

        // Remplir l'en-tête (photo + identité de la plante)
        renderHeader(scan);

        // Afficher le bloc de correspondance locale CI
        renderLocalMatch(scan.local_match);

        // Remplir les 5 cards de rapport
        renderHealthCard(scan.report?.health);
        renderEdibilityCard(scan.report?.edibility);
        renderMedicinalCard(scan.report?.medicinal);
        renderToxicityCard(scan.report?.toxicity);
        renderEnvironmentCard(scan.report?.environment);

        // Charger l'historique du chat
        await loadChatHistory(scanId);

        // ✅ Masquer le loader et afficher le contenu
        document.getElementById("loadingOverlay").classList.add("d-none");
        document.getElementById("rapportContent").classList.remove("d-none");

    } catch (error) {
        // ❌ Afficher l'erreur à la place du loader
        document.getElementById("loadingOverlay").classList.add("d-none");
        document.getElementById("errorOverlay").classList.remove("d-none");
        document.getElementById("errorOverlayMsg").textContent =
            "Erreur : " + (error.message || "Impossible de charger le rapport.");
        console.error("Erreur loadRapport:", error);
    }
}


// ============================================================
// BLOC CORRESPONDANCE LOCALE CÔTE D'IVOIRE
// ============================================================

/**
 * Affiche le bloc "Données locales CI" si une correspondance
 * a été trouvée dans notre catalogue de 18 000 plantes.
 * @param {object|null} localMatch - Les données locales (null si non trouvé)
 */
function renderLocalMatch(localMatch) {
    const block = document.getElementById("localMatchBlock");
    if (!localMatch) {
        block.classList.add("d-none");
        return;
    }

    block.classList.remove("d-none");

    document.getElementById("localMatchName").textContent = localMatch.name || "";

    const localNameEl = document.getElementById("localMatchLocalName");
    if (localMatch.local_name && !localMatch.local_name.includes("nom local")) {
        localNameEl.textContent = `(${localMatch.local_name})`;
    }

    document.getElementById("localMatchSci").textContent = localMatch.scientific_name || "";
    document.getElementById("localMatchHabitat").textContent  = localMatch.habitat  || "—";
    document.getElementById("localMatchRegions").textContent  = localMatch.regions  || "—";

    // Afficher un extrait des usages culinaires
    const cul = localMatch.culinary_uses || "—";
    document.getElementById("localMatchCulinary").textContent =
        cul.length > 80 ? cul.substring(0, 80) + "…" : cul;
}


// ============================================================
// EN-TÊTE DE LA PLANTE
// ============================================================

/**
 * Remplir l'en-tête avec la photo et les informations d'identification.
 * @param {object} scan - Les données complètes du scan
 */
function renderHeader(scan) {
    // Image de la plante
    document.getElementById("plantImage").src = `/${scan.image_path}`;

    // Nom commun et scientifique
    document.getElementById("plantName").textContent = scan.plant_name || "Plante inconnue";
    document.getElementById("plantScientific").textContent = scan.plant_scientific_name || "";

    // Famille botanique
    const familyBadge = document.getElementById("plantFamily");
    if (scan.plant_family) {
        familyBadge.textContent = `Famille : ${scan.plant_family}`;
    }

    // Score de confiance
    const confidence = (scan.confidence_score * 100).toFixed(1);
    document.getElementById("confidenceValue").textContent = `${confidence}%`;

    // Couleur de la barre selon le score
    const bar = document.getElementById("confidenceBar");
    bar.style.width = `${confidence}%`;
    if (confidence >= 80) bar.className = "progress-bar bg-success";
    else if (confidence >= 50) bar.className = "progress-bar bg-warning";
    else bar.className = "progress-bar bg-danger";

    // Badges de catégorie
    const badgesContainer = document.getElementById("categoryBadges");
    const badges = [];
    if (scan.is_toxic)    badges.push(`<span class="badge bg-danger">⚠️ Toxique (${scan.toxicity_level})</span>`);
    if (scan.is_edible)   badges.push(`<span class="badge bg-success">✅ Comestible</span>`);
    if (scan.is_medicinal) badges.push(`<span class="badge bg-info text-dark">💊 Médicinal</span>`);
    if (scan.is_invasive)  badges.push(`<span class="badge bg-warning text-dark">🌿 Invasif</span>`);
    badgesContainer.innerHTML = badges.join("");
}


// ============================================================
// CARDS DE RAPPORT
// ============================================================

/**
 * Remplir la card "Santé de la plante".
 * @param {object} health - Section health du rapport
 */
function renderHealthCard(health) {
    const el = document.getElementById("healthContent");
    if (!health) { el.innerHTML = notAvailable(); return; }

    const isBonne = health.status?.toLowerCase().includes("bonne");
    const statusClass = isBonne ? "success" : "warning";
    const statusIcon  = isBonne ? "✅" : "⚠️";

    el.innerHTML = `
        <div class="d-flex align-items-center mb-3">
            <span class="badge bg-${statusClass} fs-6 px-3 py-2">
                ${statusIcon} ${health.status || "Inconnu"}
            </span>
        </div>

        ${health.visual_signs?.length ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-eye me-1"></i>Signes visuels à observer
            </h6>
            <ul class="report-list">
                ${health.visual_signs.map(s => `<li>${s}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${health.diseases?.length && health.diseases[0] !== "Aucun connu" ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-bug me-1"></i>Maladies potentielles
            </h6>
            <ul class="report-list">
                ${health.diseases.map(d => `<li>${d}</li>`).join("")}
            </ul>
        </div>` : `<p class="text-success small"><i class="bi bi-check-circle me-1"></i>Aucune maladie connue signalée.</p>`}

        ${health.treatments?.length ? `
        <div>
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-capsule me-1"></i>Traitements recommandés
            </h6>
            <ul class="report-list">
                ${health.treatments.map(t => `<li>${t}</li>`).join("")}
            </ul>
        </div>` : ""}
    `;
}


/**
 * Remplir la card "Comestibilité".
 * @param {object} edibility - Section edibility du rapport
 */
function renderEdibilityCard(edibility) {
    const el = document.getElementById("edibilityContent");
    if (!edibility) { el.innerHTML = notAvailable(); return; }

    // Choisir le style selon le verdict
    const verdictMap = {
        "oui":     { class: "success", icon: "✅", label: "Comestible" },
        "non":     { class: "danger",  icon: "❌", label: "Non comestible" },
        "partiel": { class: "warning", icon: "⚠️", label: "Partiellement comestible" }
    };
    const verdict = verdictMap[edibility.verdict?.toLowerCase()] || verdictMap["non"];

    el.innerHTML = `
        <div class="d-flex align-items-center mb-3">
            <span class="badge bg-${verdict.class} fs-6 px-3 py-2">
                ${verdict.icon} ${verdict.label}
            </span>
        </div>

        ${edibility.edible_parts?.length ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-list-check me-1"></i>Parties comestibles
            </h6>
            <ul class="report-list">
                ${edibility.edible_parts.map(p => `<li>${p}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${edibility.recipes?.length && edibility.recipes[0] !== "Information non disponible" ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-journal-bookmark me-1"></i>Idées de recettes
            </h6>
            <ul class="report-list">
                ${edibility.recipes.map(r => `<li>${r}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${edibility.warnings?.length ? `
        <div class="alert alert-warning py-2 mb-0">
            <small><i class="bi bi-exclamation-triangle me-1"></i>
            <strong>Précautions :</strong> ${edibility.warnings.join(". ")}</small>
        </div>` : ""}
    `;
}


/**
 * Remplir la card "Propriétés médicinales".
 * @param {object} medicinal - Section medicinal du rapport
 */
function renderMedicinalCard(medicinal) {
    const el = document.getElementById("medicinalContent");
    if (!medicinal) { el.innerHTML = notAvailable(); return; }

    el.innerHTML = `
        ${medicinal.uses?.length && medicinal.uses[0] !== "Aucun connu" ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-heart me-1"></i>Usages médicinaux traditionnels
            </h6>
            <ul class="report-list">
                ${medicinal.uses.map(u => `<li>${u}</li>`).join("")}
            </ul>
        </div>` : `<p class="text-muted small">Aucun usage médicinal documenté.</p>`}

        ${medicinal.preparation?.length ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-fire me-1"></i>Modes de préparation
            </h6>
            <ul class="report-list">
                ${medicinal.preparation.map(p => `<li>${p}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${medicinal.dosage && medicinal.dosage !== "Information non disponible" ? `
        <div class="mb-3 p-2 bg-light rounded">
            <small class="fw-semibold text-muted d-block mb-1">
                <i class="bi bi-droplet me-1"></i>Posologie
            </small>
            <small>${medicinal.dosage}</small>
        </div>` : ""}

        ${medicinal.contraindications?.length ? `
        <div class="alert alert-info py-2 mb-2">
            <small><i class="bi bi-info-circle me-1"></i>
            <strong>Contre-indications :</strong></small>
            <ul class="report-list mt-1 mb-0">
                ${medicinal.contraindications.map(c => `<li><small>${c}</small></li>`).join("")}
            </ul>
        </div>` : ""}

        <div class="alert alert-warning py-2 mb-0">
            <small><i class="bi bi-shield-check me-1"></i>
            Consultez toujours un professionnel de santé avant tout usage médical.</small>
        </div>
    `;
}


/**
 * Remplir la card "Toxicité & Sécurité".
 * @param {object} toxicity - Section toxicity du rapport
 */
function renderToxicityCard(toxicity) {
    const el = document.getElementById("toxicityContent");
    if (!toxicity) { el.innerHTML = notAvailable(); return; }

    const levelMap = {
        "aucun":  { color: "success", icon: "✅", label: "Aucun danger" },
        "faible": { color: "warning", icon: "⚠️", label: "Faible" },
        "moyen":  { color: "orange",  icon: "🟠", label: "Moyen" },
        "élevé":  { color: "danger",  icon: "🔴", label: "Élevé — DANGER" },
        "inconnu":{ color: "secondary",icon: "❓", label: "Inconnu" }
    };
    const level = toxicity.level?.toLowerCase() || "inconnu";
    const lv = levelMap[level] || levelMap["inconnu"];

    el.innerHTML = `
        <div class="mb-3 p-3 rounded" style="background:var(--bs-${lv.color}-bg, #f8d7da);">
            <div class="fw-bold fs-5">${lv.icon} Toxicité : ${lv.label}</div>
        </div>

        ${toxicity.toxic_parts?.length && toxicity.toxic_parts[0] !== "Aucun connu" ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-exclamation-octagon me-1 text-danger"></i>Parties toxiques
            </h6>
            <ul class="report-list">
                ${toxicity.toxic_parts.map(p => `<li>${p}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${toxicity.symptoms?.length && toxicity.symptoms[0] !== "Information non disponible" ? `
        <div class="mb-3">
            <h6 class="fw-semibold text-muted mb-2">
                <i class="bi bi-activity me-1"></i>Symptômes d'intoxication
            </h6>
            <ul class="report-list">
                ${toxicity.symptoms.map(s => `<li>${s}</li>`).join("")}
            </ul>
        </div>` : ""}

        ${toxicity.first_aid ? `
        <div class="alert alert-danger py-2 mb-0">
            <strong><i class="bi bi-heart-pulse me-1"></i>Premiers secours :</strong>
            <p class="mb-0 mt-1 small">${toxicity.first_aid}</p>
        </div>` : ""}
    `;
}


/**
 * Remplir la card "Impact environnemental".
 * @param {object} env - Section environment du rapport
 */
function renderEnvironmentCard(env) {
    const el = document.getElementById("environmentContent");
    if (!env) { el.innerHTML = notAvailable(); return; }

    el.innerHTML = `
        <!-- Badges Invasive / Allélopathique -->
        <div class="row g-2 mb-3">
            <div class="col-6">
                <div class="p-2 rounded text-center ${env.invasive ? 'bg-warning-subtle border border-warning' : 'bg-success-subtle'}">
                    <div class="fs-4">${env.invasive ? "⚠️" : "✅"}</div>
                    <small class="fw-bold">${env.invasive ? "Espèce invasive" : "Non invasive"}</small>
                </div>
            </div>
            <div class="col-6">
                <div class="p-2 rounded text-center ${env.allelopathic ? 'bg-warning-subtle border border-warning' : 'bg-success-subtle'}">
                    <div class="fs-4">${env.allelopathic ? "⚠️" : "✅"}</div>
                    <small class="fw-bold">${env.allelopathic ? "Allélopathique" : "Non allélopathique"}</small>
                </div>
            </div>
        </div>

        ${env.allelopathic && env.allelopathic_detail && env.allelopathic_detail !== "Non allélopathique" ? `
        <div class="alert alert-warning py-2 mb-3">
            <small><i class="bi bi-info-circle me-1"></i><strong>Effet allélopathique :</strong> ${env.allelopathic_detail}</small>
        </div>` : ""}

        ${env.soil_impact && env.soil_impact !== "Information non disponible" ? `
        <div class="mb-2">
            <h6 class="fw-semibold text-muted mb-1">
                <i class="bi bi-layers me-1"></i>Impact sur le sol
            </h6>
            <p class="mb-0 small">${env.soil_impact}</p>
        </div>` : ""}

        ${env.agricultural_impact && env.agricultural_impact !== "Information non disponible" ? `
        <div class="mt-3">
            <h6 class="fw-semibold text-muted mb-1">
                <i class="bi bi-flower3 me-1"></i>Impact sur l'agriculture
            </h6>
            <p class="mb-0 small">${env.agricultural_impact}</p>
        </div>` : ""}
    `;
}


// ============================================================
// UTILITAIRE
// ============================================================

/**
 * HTML affiché quand une section du rapport n'est pas disponible.
 */
function notAvailable() {
    return `<p class="text-muted small text-center py-3">
        <i class="bi bi-hourglass me-1"></i>Information non disponible
    </p>`;
}
