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

    // Générer une card Bootstrap pour chaque scan
    grid.innerHTML = scans.map(scan => `
        <div class="col-md-4 col-lg-3" id="scanCard_${scan.id}">
            <div class="card border-0 shadow-sm h-100 scan-card position-relative">

                <!-- Bouton suppression (visible au survol via CSS) -->
                <button class="btn btn-danger btn-sm btn-delete position-absolute top-0 end-0 m-2 rounded-circle"
                        style="width:32px;height:32px;padding:0;z-index:1;"
                        onclick="openDeleteModal(${scan.id}, event)"
                        title="Supprimer ce scan">
                    <i class="bi bi-trash"></i>
                </button>

                <!-- Image -->
                <img src="/${scan.image_path}" class="card-img-top"
                     style="height:180px;object-fit:cover;cursor:pointer;"
                     onclick="viewRapport(${scan.id})"
                     onerror="this.src='https://via.placeholder.com/300x180/e9ecef/6c757d?text=Image+non+disponible'">

                <!-- Corps de la card -->
                <div class="card-body p-3" style="cursor:pointer;" onclick="viewRapport(${scan.id})">
                    <h6 class="fw-bold mb-1 text-truncate" title="${scan.plant_name}">
                        ${scan.plant_name || "Plante inconnue"}
                    </h6>
                    <small class="text-muted fst-italic d-block mb-2 text-truncate">
                        ${scan.plant_scientific_name || ""}
                    </small>

                    <!-- Badges -->
                    <div class="d-flex flex-wrap gap-1 mb-2">
                        ${scan.is_toxic
                            ? `<span class="badge bg-danger plant-tag">⚠️ Toxique</span>`
                            : ""}
                        ${scan.is_edible
                            ? `<span class="badge bg-success plant-tag">✅ Comestible</span>`
                            : ""}
                        ${scan.is_medicinal
                            ? `<span class="badge bg-info text-dark plant-tag">💊 Médicinal</span>`
                            : ""}
                        ${scan.is_invasive
                            ? `<span class="badge bg-warning text-dark plant-tag">🌿 Invasif</span>`
                            : ""}
                        ${!scan.is_toxic && !scan.is_edible && !scan.is_medicinal && !scan.is_invasive
                            ? `<span class="badge bg-secondary plant-tag">Non classifié</span>`
                            : ""}
                    </div>

                    <!-- Score de confiance -->
                    <div class="d-flex align-items-center gap-2">
                        <div class="progress flex-grow-1" style="height:4px;">
                            <div class="progress-bar ${scan.confidence_score >= 0.8 ? 'bg-success' : scan.confidence_score >= 0.5 ? 'bg-warning' : 'bg-danger'}"
                                 style="width:${scan.confidence_score * 100}%"></div>
                        </div>
                        <small class="text-muted">${(scan.confidence_score * 100).toFixed(0)}%</small>
                    </div>
                </div>

                <!-- Pied de card : date + localisation -->
                <div class="card-footer bg-transparent border-0 text-muted small p-3 pt-0">
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
                        <span><i class="bi bi-calendar3 me-1"></i>${formatDate(scan.created_at)}</span>
                        ${scan.latitude && scan.longitude
                            ? `<a href="https://www.openstreetmap.org/?mlat=${scan.latitude}&mlon=${scan.longitude}&zoom=15"
                                  target="_blank" class="text-success text-decoration-none"
                                  id="geo-${scan.id}"
                                  title="Voir sur la carte (${scan.latitude.toFixed(4)}, ${scan.longitude.toFixed(4)})">
                                  <i class="bi bi-geo-alt-fill"></i>
                                  <span class="geo-label">Chargement...</span>
                               </a>`
                            : `<span class="text-muted opacity-50"><i class="bi bi-geo-alt"></i> Non localisé</span>`
                        }
                    </div>
                </div>
            </div>
        </div>
    `).join("");

    // Mettre à jour la pagination
    renderPagination(scans.length);

    // Charger les noms de lieux pour les scans géolocalisés
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

    // Mettre à jour les styles des boutons de filtre
    document.querySelectorAll(".btn-group .btn").forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");

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
    const grid = document.getElementById("scansGrid");
    grid.innerHTML = Array(4).fill(`
        <div class="col-md-4 col-lg-3 skeleton-card">
            <div class="card border-0 shadow-sm placeholder-glow">
                <div class="placeholder" style="height:180px;border-radius:8px 8px 0 0;"></div>
                <div class="card-body">
                    <div class="placeholder col-8 mb-2"></div>
                    <div class="placeholder col-5 mb-2"></div>
                    <div class="placeholder col-6"></div>
                </div>
            </div>
        </div>
    `).join("");
    document.getElementById("noResultsMessage").classList.add("d-none");
}

/** Afficher le message "aucun résultat". */
function showNoResults() {
    document.getElementById("scansGrid").innerHTML = "";
    document.getElementById("noResultsMessage").classList.remove("d-none");
    document.getElementById("pagination").innerHTML = "";
}
