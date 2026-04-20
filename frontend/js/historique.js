// ============================================================
// FICHIER : frontend/js/historique.js
// RÔLE    : Gestion de la page historique (historique.html)
//           Liste paginée des scans avec filtres et suppression
// ============================================================

// Variables d'état de la page
let currentPage   = 1;    // Page courante de la pagination
let currentFilter = "";   // Filtre actif ("", "toxic", "edible"...)
let searchTimeout = null; // Timer pour la recherche (évite trop d'appels API)
let totalScans    = 0;    // Nombre total de scans (pour la pagination)
const LIMIT       = 12;   // Scans par page

// ID du scan en cours de suppression (pour le modal)
let scanToDelete = null;

// Cache reverse geocoding : {"{lat},{lng}": "Abidjan, CI"}
const geoCache = {};

// ============================================================
// INITIALISATION
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
    if (!requireAuth()) return;
    loadNavUser();
    await loadScans();

    // Initialiser le modal de suppression
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    if (confirmBtn) {
        confirmBtn.addEventListener("click", confirmDelete);
    }
});


// ============================================================
// CHARGEMENT DES SCANS
// ============================================================

/**
 * Charger et afficher les scans depuis l'API.
 * Applique les filtres et la pagination en cours.
 */
async function loadScans() {
    showSkeletons();

    try {
        // Construire l'URL avec les paramètres de filtrage et pagination
        let url = `/api/scan/history?page=${currentPage}&limit=${LIMIT}`;
        if (currentFilter) url += `&filter_type=${currentFilter}`;

        const scans = await apiGet(url);

        // Mettre à jour le compteur total
        // Note: une vraie pagination nécessiterait un endpoint /count
        // Ici on estime : si on a exactement LIMIT résultats, il peut y en avoir plus
        totalScans = scans.length;

        // Afficher les scans ou le message "aucun résultat"
        if (scans.length === 0) {
            showNoResults();
        } else {
            renderScans(scans);
        }

        // Mettre à jour le compteur dans le titre
        document.getElementById("totalCount").textContent =
            scans.length < LIMIT ? (currentPage - 1) * LIMIT + scans.length : "...";

    } catch (error) {
        showToast("Erreur lors du chargement : " + error.message, "danger");
        showNoResults();
    }
}


// ============================================================
// AFFICHAGE DES SCANS
// ============================================================

/**
 * Afficher la grille de cards de scans.
 * @param {Array} scans - Tableau d'objets scan
 */
function renderScans(scans) {
    const grid = document.getElementById("scansGrid");
    document.getElementById("noResultsMessage").classList.add("d-none");

    // Cacher le skeleton statique et afficher la vraie grille
    const skeleton = document.getElementById("scanSkeleton");
    if (skeleton) skeleton.classList.add("d-none");
    grid.classList.remove("d-none");

    grid.innerHTML = scans.map(scan => {
        const conf = (scan.confidence_score * 100).toFixed(0);
        const confColor = scan.confidence_score >= 0.8 ? '#198754'
                        : scan.confidence_score >= 0.5 ? '#ffc107' : '#dc3545';
        const badges = [
            scan.is_toxic     ? `<span class="badge-pill bg-danger bg-opacity-15 text-danger">⚠️ Toxique</span>`    : "",
            scan.is_edible    ? `<span class="badge-pill bg-success bg-opacity-15 text-success">✅ Comestible</span>` : "",
            scan.is_medicinal ? `<span class="badge-pill bg-info bg-opacity-15 text-info">💊 Médicinal</span>`       : "",
            scan.is_invasive  ? `<span class="badge-pill bg-warning bg-opacity-15 text-warning">🌿 Invasif</span>`   : "",
        ].filter(Boolean).join("") || `<span class="badge-pill bg-secondary bg-opacity-15 text-secondary">Non classifié</span>`;

        return `
        <div class="col-6 col-md-4 col-lg-3" id="scanCard_${scan.id}">
            <div class="scan-card-new position-relative" onclick="viewRapport(${scan.id})">
                <!-- Badge confiance -->
                <div class="conf-badge">${conf}%</div>
                <!-- Bouton suppression -->
                <button class="del-btn" onclick="openDeleteModal(${scan.id}, event)" title="Supprimer">
                    <i class="bi bi-trash"></i>
                </button>
                <!-- Image -->
                <img src="/${scan.image_path}?token=${localStorage.getItem('access_token')}" alt="${scan.plant_name}"
                     onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22170%22%3E%3Crect width=%22300%22 height=%22170%22 fill=%22%23e9ecef%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%239ca3af%22 font-size=%2240%22%3E🌿%3C/text%3E%3C/svg%3E'">
                <!-- Contenu -->
                <div class="card-content">
                    <div class="plant-name" title="${scan.plant_name}">${scan.plant_name || "Plante inconnue"}</div>
                    <div class="plant-sci">${scan.plant_scientific_name || ""}</div>
                    <div class="plant-badges mb-2">${badges}</div>
                    <div class="d-flex align-items-center gap-2">
                        <div style="flex:1;height:4px;background:#f0f0f0;border-radius:2px;overflow:hidden;">
                            <div style="height:100%;width:${conf}%;background:${confColor};border-radius:2px;"></div>
                        </div>
                        <small style="color:${confColor};font-weight:700;font-size:0.72rem;">${conf}%</small>
                    </div>
                    <div class="mt-2" style="font-size:0.72rem;color:#9ca3af;">
                        <i class="bi bi-calendar3 me-1"></i>${formatDate(scan.created_at)}
                        ${scan.latitude && scan.longitude
                            ? `<a href="https://www.openstreetmap.org/?mlat=${scan.latitude}&mlon=${scan.longitude}&zoom=15"
                                  target="_blank" class="ms-2 text-success text-decoration-none"
                                  id="geo-${scan.id}" onclick="event.stopPropagation()">
                                  <i class="bi bi-geo-alt-fill"></i>
                                  <span class="geo-label">…</span>
                               </a>`
                            : ""}
                    </div>
                </div>
            </div>
        </div>`;
    }).join("");

    renderPagination(scans.length);

    scans.forEach(scan => {
        if (scan.latitude && scan.longitude) {
            resolveGeoLabel(scan.id, scan.latitude, scan.longitude);
        }
    });
}


// ============================================================
// REVERSE GEOCODING (lat/lng → nom de ville)
// ============================================================

/**
 * Résout la position GPS en nom de lieu et met à jour le label.
 * Utilise OpenStreetMap Nominatim (gratuit, sans clé API).
 */
async function resolveGeoLabel(scanId, lat, lng) {
    const key = `${lat.toFixed(4)},${lng.toFixed(4)}`;

    // Utiliser le cache si disponible
    if (geoCache[key]) {
        updateGeoLabel(scanId, geoCache[key]);
        return;
    }

    try {
        const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&accept-language=fr`,
            { headers: { "Accept-Language": "fr" } }
        );
        const data = await res.json();

        // Extraire ville ou région la plus précise disponible
        const addr = data.address || {};
        const lieu =
            addr.city       ||
            addr.town       ||
            addr.village    ||
            addr.suburb     ||
            addr.county     ||
            addr.state      ||
            addr.country    ||
            `${lat.toFixed(3)}, ${lng.toFixed(3)}`;

        // Ajouter le pays si différent de la ville
        const pays = addr.country_code ? addr.country_code.toUpperCase() : "";
        const label = pays && lieu !== addr.country ? `${lieu}, ${pays}` : lieu;

        geoCache[key] = label;
        updateGeoLabel(scanId, label);

    } catch (e) {
        // En cas d'erreur réseau → afficher les coordonnées brutes
        const label = `${lat.toFixed(3)}, ${lng.toFixed(3)}`;
        geoCache[key] = label;
        updateGeoLabel(scanId, label);
    }
}

/**
 * Met à jour le texte du label GPS dans la card.
 */
function updateGeoLabel(scanId, label) {
    const el = document.querySelector(`#geo-${scanId} .geo-label`);
    if (el) el.textContent = label;
}


// ============================================================
// FILTRES
// ============================================================

/**
 * Appliquer un filtre et recharger les scans.
 * @param {string} filter - "" | "toxic" | "edible" | "medicinal" | "invasive"
 * @param {HTMLElement} btn - Le bouton cliqué (pour le style actif)
 */
function applyFilter(filter, btn) {
    currentFilter = filter;
    currentPage   = 1;

    // Retirer toutes les classes actives des pills
    document.querySelectorAll(".filter-pill").forEach(b => {
        b.className = "filter-pill"; // reset
    });

    // Appliquer la bonne classe active selon le filtre
    if (btn) {
        const activeClass = {
            "":         "active-all",
            "toxic":    "active-toxic",
            "edible":   "active-edible",
            "medicinal":"active-medic",
            "invasive": "active-inv",
        }[filter] || "active-all";
        btn.classList.add(activeClass);
    }

    loadScans();
}


/**
 * Gérer la saisie dans la barre de recherche.
 * Utilise un délai (debounce) pour ne pas appeler l'API à chaque frappe.
 * @param {string} value - La valeur saisie
 */
function onSearchInput(value) {
    // Annuler le timer précédent
    clearTimeout(searchTimeout);

    // Attendre 500ms après la dernière frappe avant de lancer la recherche
    // Cela évite d'appeler l'API pour chaque lettre tapée
    searchTimeout = setTimeout(() => {
        // Pour l'instant, on filtre côté client sur les scans chargés
        filterDisplayedScans(value.toLowerCase());
    }, 300);
}


/**
 * Filtrer les cards affichées côté client (sans appel API).
 * @param {string} query - Terme de recherche en minuscules
 */
function filterDisplayedScans(query) {
    const cards = document.querySelectorAll("[id^='scanCard_']");
    let visibleCount = 0;

    cards.forEach(card => {
        // Chercher dans le nom commun et scientifique
        const text = card.textContent.toLowerCase();
        const matches = !query || text.includes(query);

        card.style.display = matches ? "" : "none";
        if (matches) visibleCount++;
    });

    // Afficher le message "aucun résultat" si nécessaire
    document.getElementById("noResultsMessage").classList.toggle("d-none", visibleCount > 0);
}


// ============================================================
// PAGINATION
// ============================================================

/**
 * Afficher les boutons de pagination.
 * @param {number} count - Nombre de résultats sur la page courante
 */
function renderPagination(count) {
    const nav  = document.getElementById("paginationNav");
    const ul   = document.getElementById("pagination");

    // Cacher la pagination si une seule page
    if (count < LIMIT && currentPage === 1) {
        nav.style.display = "none";
        return;
    }
    nav.style.display = "";

    ul.innerHTML = `
        <!-- Bouton Précédent -->
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <button class="page-link" onclick="changePage(${currentPage - 1})">
                <i class="bi bi-chevron-left"></i>
            </button>
        </li>

        <!-- Numéro de page courant -->
        <li class="page-item active">
            <span class="page-link bg-success border-success">Page ${currentPage}</span>
        </li>

        <!-- Bouton Suivant -->
        <li class="page-item ${count < LIMIT ? 'disabled' : ''}">
            <button class="page-link" onclick="changePage(${currentPage + 1})">
                <i class="bi bi-chevron-right"></i>
            </button>
        </li>
    `;
}


/**
 * Changer de page.
 * @param {number} page - Numéro de la nouvelle page
 */
function changePage(page) {
    if (page < 1) return;
    currentPage = page;

    // Remonter en haut de la page
    window.scrollTo({ top: 0, behavior: "smooth" });

    loadScans();
}


// ============================================================
// SUPPRESSION
// ============================================================

/**
 * Ouvrir le modal de confirmation de suppression.
 * @param {number} scanId - L'ID du scan à supprimer
 * @param {Event} event   - L'événement click (pour stopper la propagation)
 */
function openDeleteModal(scanId, event) {
    // Empêcher le clic de naviguer vers le rapport
    event.stopPropagation();

    scanToDelete = scanId;

    // Ouvrir le modal Bootstrap
    const modal = new bootstrap.Modal(document.getElementById("deleteModal"));
    modal.show();
}


/**
 * Confirmer et exécuter la suppression du scan.
 */
async function confirmDelete() {
    if (!scanToDelete) return;

    try {
        await apiDelete(`/api/scan/${scanToDelete}`);

        // Fermer le modal
        bootstrap.Modal.getInstance(document.getElementById("deleteModal")).hide();

        // Supprimer la card de l'interface sans recharger la page
        const card = document.getElementById(`scanCard_${scanToDelete}`);
        if (card) {
            // Animation de disparition avant suppression
            card.style.transition = "opacity 0.3s, transform 0.3s";
            card.style.opacity = "0";
            card.style.transform = "scale(0.9)";
            setTimeout(() => card.remove(), 300);
        }

        showToast("Scan supprimé avec succès.", "success");
        scanToDelete = null;

    } catch (error) {
        showToast("Erreur lors de la suppression : " + error.message, "danger");
    }
}


// ============================================================
// UTILITAIRES
// ============================================================

/** Naviguer vers la page de rapport d'un scan. */
function viewRapport(scanId) {
    window.location.href = `/rapport?id=${scanId}`;
}

/** Afficher les skeletons de chargement. */
function showSkeletons() {
    // Montrer le skeleton statique, cacher la vraie grille
    const skeleton = document.getElementById("scanSkeleton");
    if (skeleton) skeleton.classList.remove("d-none");
    document.getElementById("scansGrid").classList.add("d-none");
    document.getElementById("noResultsMessage").classList.add("d-none");
}

/** Afficher le message "aucun résultat". */
function showNoResults() {
    const skeleton = document.getElementById("scanSkeleton");
    if (skeleton) skeleton.classList.add("d-none");
    document.getElementById("scansGrid").classList.add("d-none");
    document.getElementById("scansGrid").innerHTML = "";
    document.getElementById("noResultsMessage").classList.remove("d-none");
    document.getElementById("pagination").innerHTML = "";
}
