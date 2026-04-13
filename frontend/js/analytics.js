// ============================================================
// FICHIER : frontend/js/analytics.js
// RÔLE    : Tableau de bord analytique (analytics.html)
//           Affiche des graphiques Chart.js à partir des données API
//
// CONCEPT POUR DÉBUTANT :
//   Chart.js est une bibliothèque JavaScript qui dessine des graphiques
//   dans un élément HTML <canvas>.
//   On lui passe des données et une configuration, et il gère tout.
// ============================================================

// Stocker les instances de graphiques pour pouvoir les mettre à jour
let distributionChart  = null;
let timelineChart      = null;
let topPlantsChart     = null;
let diseasesChart      = null;
let scanMap            = null;   // Instance Leaflet

// Graphiques globaux
let gDistributionChart = null;
let gTopPlantsChart    = null;
let gDiseasesChart     = null;
let gRiskMap           = null;
let globalLoaded       = false;  // Charger les données globales une seule fois

// ============================================================
// INITIALISATION
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
    if (!requireAuth()) return;
    loadNavUser();
    await Promise.all([
        loadSummary(),
        loadDistribution(),
        loadTimeline(30),
        loadTopPlants(),
        loadDiseases(),
        loadAlerts(),
        loadMap()
    ]);
    // Promise.all exécute toutes les requêtes en parallèle
    // C'est plus rapide qu'attendre chaque requête l'une après l'autre
});


// ============================================================
// CHARGEMENT DES DONNÉES
// ============================================================

/**
 * Charger et afficher les KPI (indicateurs clés).
 */
async function loadSummary() {
    try {
        const data = await apiGet("/api/analytics/summary");

        document.getElementById("kpiTotalScans").textContent  = data.total_scans;
        document.getElementById("kpiUniquePlants").textContent = data.unique_plants;
        document.getElementById("kpiEdible").textContent      = data.edible_plants_count;
        document.getElementById("kpiToxic").textContent       = data.toxic_plants_count;
        document.getElementById("kpiMedicinal").textContent   = data.medicinal_plants_count;
        document.getElementById("kpiInvasive").textContent    = data.invasive_plants_count;

    } catch (error) {
        console.error("Erreur chargement summary:", error);
    }
}


/**
 * Charger et afficher le graphique de répartition (donut).
 */
async function loadDistribution() {
    try {
        const data = await apiGet("/api/analytics/distribution");

        const canvas = document.getElementById("distributionChart");
        const ctx    = canvas.getContext("2d");  // "2d" = contexte de rendu 2D

        // Détruire l'ancien graphique s'il existe (évite les doublons)
        if (distributionChart) distributionChart.destroy();

        // Créer le graphique en donut (anneau)
        distributionChart = new Chart(ctx, {
            type: "doughnut",   // Type de graphique : donut/anneau
            data: {
                labels: data.labels,  // ["Comestibles", "Toxiques", ...]
                datasets: [{
                    data: data.values,  // [45, 20, 35, 5]
                    backgroundColor: [
                        "#198754",   // Vert pour comestibles
                        "#dc3545",   // Rouge pour toxiques
                        "#0dcaf0",   // Bleu pour médicinales
                        "#ffc107"    // Jaune pour invasives
                    ],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: "bottom",  // Légende en bas du graphique
                        labels: {
                            padding: 15,
                            usePointStyle: true  // Points ronds au lieu de rectangles
                        }
                    },
                    tooltip: {
                        callbacks: {
                            // Personnaliser l'affichage du tooltip (bulle au survol)
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct   = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${context.parsed} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Erreur chargement distribution:", error);
    }
}


/**
 * Charger et afficher le graphique d'évolution temporelle (courbe).
 * @param {number} days - Nombre de jours à afficher (7, 30, 90)
 */
async function loadTimeline(days = 30) {
    try {
        const data = await apiGet(`/api/analytics/timeline?days=${days}`);

        const canvas = document.getElementById("timelineChart");
        const ctx    = canvas.getContext("2d");

        if (timelineChart) timelineChart.destroy();

        // Extraire les labels (dates) et les valeurs (comptages)
        const labels = data.map(point => {
            // Formater la date pour l'affichage : "2024-01-15" → "15/01"
            const [year, month, day] = point.date.split("-");
            return `${day}/${month}`;
        });
        const values = data.map(point => point.count);

        timelineChart = new Chart(ctx, {
            type: "line",   // Graphique en courbe
            data: {
                labels,
                datasets: [{
                    label: "Analyses",
                    data: values,
                    borderColor: "#198754",          // Couleur de la ligne
                    backgroundColor: "rgba(25,135,84,0.1)",  // Remplissage sous la ligne
                    borderWidth: 2,
                    fill: true,          // Remplir sous la courbe
                    tension: 0.4,        // Courbe lissée (0 = angles droits)
                    pointBackgroundColor: "#198754",
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                scales: {
                    // Axe Y : commencer à 0, valeurs entières
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    // Axe X : afficher moins de labels pour éviter la surcharge
                    x: {
                        ticks: {
                            maxTicksLimit: 10,
                            maxRotation: 45
                        }
                    }
                },
                plugins: {
                    legend: { display: false }  // Pas de légende (une seule courbe)
                }
            }
        });

    } catch (error) {
        console.error("Erreur chargement timeline:", error);
    }
}


/**
 * Charger et afficher le graphique des top plantes (barres horizontales).
 */
async function loadTopPlants() {
    try {
        const data = await apiGet("/api/analytics/top-plants?limit=10");

        const canvas = document.getElementById("topPlantsChart");
        const ctx    = canvas.getContext("2d");

        if (topPlantsChart) topPlantsChart.destroy();

        // Limiter les noms trop longs pour les labels
        const labels = data.map(p =>
            p.plant_name.length > 20 ? p.plant_name.substring(0, 20) + "..." : p.plant_name
        );
        const values = data.map(p => p.scan_count);

        topPlantsChart = new Chart(ctx, {
            type: "bar",   // Graphique en barres
            data: {
                labels,
                datasets: [{
                    label: "Nombre de scans",
                    data: values,
                    backgroundColor: "rgba(25,135,84,0.7)",
                    borderColor: "#198754",
                    borderWidth: 1,
                    borderRadius: 4  // Coins arrondis des barres
                }]
            },
            options: {
                indexAxis: "y",   // "y" = barres horizontales (plus lisible pour les noms)
                responsive: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

    } catch (error) {
        console.error("Erreur chargement top plants:", error);
    }
}


/**
 * Charger et afficher le graphique des maladies les plus fréquentes.
 */
async function loadDiseases() {
    try {
        const data = await apiGet("/api/analytics/diseases?limit=10");

        const noData = document.getElementById("noDiseasesData");
        const canvas = document.getElementById("diseasesChart");

        if (!data || data.length === 0) {
            canvas.classList.add("d-none");
            noData.classList.remove("d-none");
            return;
        }

        noData.classList.add("d-none");
        canvas.classList.remove("d-none");

        const ctx = canvas.getContext("2d");
        if (diseasesChart) diseasesChart.destroy();

        const labels = data.map(d =>
            d.disease.length > 25 ? d.disease.substring(0, 25) + "…" : d.disease
        );
        const values = data.map(d => d.count);

        // Palette de rouges/oranges pour les maladies
        const colors = values.map((_, i) => {
            const palette = ["#dc3545","#e85d6a","#f28b30","#fd7e14","#ffc107",
                             "#e63946","#c1121f","#ff6b6b","#ff9f43","#ee5a24"];
            return palette[i % palette.length];
        });

        diseasesChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Occurrences",
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                scales: {
                    x: { beginAtZero: true, ticks: { stepSize: 1 } }
                },
                plugins: { legend: { display: false } }
            }
        });

    } catch (error) {
        console.error("Erreur chargement maladies:", error);
    }
}


/**
 * Charger et afficher les alertes (ponctuelles + tendances).
 */
async function loadAlerts() {
    try {
        const data = await apiGet("/api/analytics/alerts");

        // ---- Alertes ponctuelles ----
        const list    = document.getElementById("alertsList");
        const noAlert = document.getElementById("noAlerts");

        if (data.count === 0) {
            list.innerHTML = "";
            noAlert.classList.remove("d-none");
        } else {
            noAlert.classList.add("d-none");
            list.innerHTML = data.alerts.map(alert => {
                const isToxic = alert.alert_types.includes("Toxicité élevée");
                const itemClass = isToxic ? "alert-item-toxic" : "alert-item-invasive";
                return `
                    <a href="/rapport?id=${alert.scan_id}"
                       class="list-group-item list-group-item-action ${itemClass} py-3">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1 fw-semibold">${alert.plant_name}</h6>
                                <small class="text-muted fst-italic">${alert.scientific_name}</small>
                                <div class="mt-1">
                                    ${alert.alert_types.map(type =>
                                        `<span class="badge ${type.includes("Toxicité") ? "bg-danger" : "bg-warning text-dark"} me-1">${type}</span>`
                                    ).join("")}
                                </div>
                            </div>
                            <small class="text-muted">${alert.date}</small>
                        </div>
                    </a>`;
            }).join("");
        }

        // ---- Alertes de tendance ----
        const trendList    = document.getElementById("trendAlertsList");
        const noTrendAlert = document.getElementById("noTrendAlerts");
        const trends       = data.trend_alerts || [];

        if (trends.length === 0) {
            trendList.innerHTML = "";
            noTrendAlert.classList.remove("d-none");
        } else {
            noTrendAlert.classList.add("d-none");

            const severityConfig = {
                danger:  { bg: "bg-danger-subtle",  text: "text-danger",  icon: "bi-exclamation-triangle-fill" },
                warning: { bg: "bg-warning-subtle", text: "text-warning", icon: "bi-exclamation-circle-fill"   },
                info:    { bg: "bg-info-subtle",    text: "text-info",    icon: "bi-info-circle-fill"          }
            };

            trendList.innerHTML = trends.map(t => {
                const cfg  = severityConfig[t.severity] || severityConfig.warning;
                const arrow = t.current_week > t.prev_week ? "↑" : "↓";
                return `
                    <div class="list-group-item ${cfg.bg} py-3 border-0">
                        <div class="d-flex align-items-start gap-2">
                            <i class="bi ${cfg.icon} ${cfg.text} mt-1"></i>
                            <div>
                                <p class="mb-1 fw-semibold small">${t.message}</p>
                                <div class="d-flex gap-3 small text-muted">
                                    <span>Cette semaine : <strong class="${cfg.text}">${t.current_week}</strong></span>
                                    <span>Semaine préc. : <strong>${t.prev_week}</strong></span>
                                    <span class="${cfg.text} fw-bold">${arrow}</span>
                                </div>
                            </div>
                        </div>
                    </div>`;
            }).join("");
        }

    } catch (error) {
        console.error("Erreur chargement alertes:", error);
    }
}


// ============================================================
// GESTION DES ONGLETS (Mes stats / Global)
// ============================================================

function switchTab(tab) {
    const myView     = document.getElementById("viewMyStats");
    const globalView = document.getElementById("viewGlobal");
    const tabMy      = document.getElementById("tabMyStats");
    const tabGlobal  = document.getElementById("tabGlobal");

    if (tab === "my") {
        myView.classList.remove("d-none");
        globalView.classList.add("d-none");
        tabMy.classList.add("active");
        tabGlobal.classList.remove("active");
    } else {
        myView.classList.add("d-none");
        globalView.classList.remove("d-none");
        tabMy.classList.remove("active");
        tabGlobal.classList.add("active");

        // Charger les données globales seulement au premier clic
        if (!globalLoaded) {
            globalLoaded = true;
            Promise.all([
                loadGlobalSummary(),
                loadGlobalDistribution(),
                loadGlobalTopPlants(),
                loadGlobalDiseases(),
                loadGlobalRiskMap()
            ]);
        }
    }
}


// ============================================================
// STATISTIQUES GLOBALES
// ============================================================

async function loadGlobalSummary() {
    try {
        const data = await apiGet("/api/analytics/global/summary");
        document.getElementById("gKpiScans").textContent    = data.total_scans;
        document.getElementById("gKpiUnique").textContent   = data.unique_plants;
        document.getElementById("gKpiEdible").textContent   = data.edible_plants_count;
        document.getElementById("gKpiToxic").textContent    = data.toxic_plants_count;
        document.getElementById("gKpiInvasive").textContent = data.invasive_plants_count;
    } catch (e) {
        console.error("Erreur global summary:", e);
    }
}

async function loadGlobalDistribution() {
    try {
        const data = await apiGet("/api/analytics/global/distribution");
        const ctx  = document.getElementById("gDistributionChart").getContext("2d");
        if (gDistributionChart) gDistributionChart.destroy();

        gDistributionChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: ["#198754","#dc3545","#0dcaf0","#ffc107"],
                    borderWidth: 2,
                    borderColor: "#fff"
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "bottom", labels: { padding: 15, usePointStyle: true } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct   = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.error("Erreur global distribution:", e);
    }
}

async function loadGlobalTopPlants() {
    try {
        const data = await apiGet("/api/analytics/global/top-plants?limit=10");
        const ctx  = document.getElementById("gTopPlantsChart").getContext("2d");
        if (gTopPlantsChart) gTopPlantsChart.destroy();

        const labels = data.map(p =>
            p.plant_name.length > 22 ? p.plant_name.substring(0, 22) + "…" : p.plant_name
        );

        gTopPlantsChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Scans",
                    data: data.map(p => p.scan_count),
                    backgroundColor: "rgba(25,135,84,0.75)",
                    borderColor: "#198754",
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } },
                plugins: { legend: { display: false } }
            }
        });
    } catch (e) {
        console.error("Erreur global top plants:", e);
    }
}

async function loadGlobalDiseases() {
    try {
        const data   = await apiGet("/api/analytics/global/diseases?limit=10");
        const canvas = document.getElementById("gDiseasesChart");
        const noData = document.getElementById("gNoDiseasesData");

        if (!data || data.length === 0) {
            canvas.classList.add("d-none");
            noData.classList.remove("d-none");
            return;
        }

        noData.classList.add("d-none");
        canvas.classList.remove("d-none");
        const ctx = canvas.getContext("2d");
        if (gDiseasesChart) gDiseasesChart.destroy();

        const palette = ["#dc3545","#e85d6a","#f28b30","#fd7e14","#ffc107",
                         "#e63946","#c1121f","#ff6b6b","#ff9f43","#ee5a24"];

        gDiseasesChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.map(d => d.disease.length > 25 ? d.disease.substring(0,25)+"…" : d.disease),
                datasets: [{
                    label: "Occurrences",
                    data: data.map(d => d.count),
                    backgroundColor: data.map((_, i) => palette[i % palette.length]),
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } },
                plugins: { legend: { display: false } }
            }
        });
    } catch (e) {
        console.error("Erreur global diseases:", e);
    }
}

async function loadGlobalRiskMap() {
    try {
        const data    = await apiGet("/api/analytics/global/regions-at-risk");
        const mapDiv  = document.getElementById("gRiskMap");
        const noData  = document.getElementById("gMapNoData");

        if (!data.zones || data.zones.length === 0) {
            mapDiv.classList.add("d-none");
            noData.classList.remove("d-none");
            return;
        }

        if (gRiskMap) {
            gRiskMap.remove();
            gRiskMap = null;
        }

        gRiskMap = L.map("gRiskMap").setView([7.54, -5.55], 6);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        }).addTo(gRiskMap);

        const bounds = [];
        data.zones.forEach(zone => {
            // Rayon proportionnel au nombre de cas (min 8km, max 40km)
            const radius = Math.min(8000 + zone.total * 3000, 40000);
            // Rouge si toxique domine, orange si invasif
            const color  = zone.toxic >= zone.invasive ? "#dc3545" : "#fd7e14";

            L.circle([zone.lat, zone.lng], {
                radius,
                color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 2
            }).bindPopup(`
                <strong>Zone à risque</strong><br>
                <span class="badge bg-danger me-1">Toxiques : ${zone.toxic}</span>
                <span class="badge bg-warning text-dark">Invasives : ${zone.invasive}</span><br>
                <small class="text-muted">Total scans : ${zone.total}</small>
            `).addTo(gRiskMap);

            bounds.push([zone.lat, zone.lng]);
        });

        if (bounds.length > 1) gRiskMap.fitBounds(bounds, { padding: [30, 30] });

    } catch (e) {
        console.error("Erreur global risk map:", e);
    }
}


// ============================================================
// CARTE DES SCANS (Leaflet.js + OpenStreetMap)
// ============================================================

async function loadMap() {
    try {
        const data = await apiGet("/api/analytics/locations");

        // Mettre à jour le compteur
        document.getElementById("mapPointCount").textContent =
            `${data.total} scan${data.total > 1 ? "s" : ""} géolocalisé${data.total > 1 ? "s" : ""}`;

        // Pas de données → afficher message
        if (!data.points || data.points.length === 0) {
            document.getElementById("scanMap").classList.add("d-none");
            document.getElementById("mapNoData").classList.remove("d-none");
            return;
        }

        // Initialiser la carte Leaflet (centré sur la Côte d'Ivoire par défaut)
        const defaultCenter = [7.539989, -5.547080];
        const defaultZoom   = data.points.length === 1 ? 13 : 6;

        scanMap = L.map("scanMap").setView(defaultCenter, defaultZoom);

        // Tuiles OpenStreetMap (gratuit, sans clé API)
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        }).addTo(scanMap);

        // Couleur du marqueur selon le type de plante
        function markerColor(point) {
            if (point.is_toxic)    return "#dc3545";  // rouge
            if (point.is_invasive) return "#fd7e14";  // orange
            if (point.is_edible)   return "#198754";  // vert
            if (point.is_medicinal)return "#0dcaf0";  // bleu clair
            return "#6c757d";                          // gris
        }

        // Créer une icône personnalisée (cercle coloré)
        function createIcon(color) {
            return L.divIcon({
                className: "",
                html: `<div style="
                    width:14px; height:14px; border-radius:50%;
                    background:${color}; border:2px solid white;
                    box-shadow:0 2px 6px rgba(0,0,0,0.35);
                "></div>`,
                iconSize:   [14, 14],
                iconAnchor: [7, 7]
            });
        }

        const bounds = [];

        // Ajouter chaque scan sur la carte
        data.points.forEach(point => {
            const color = markerColor(point);
            const marker = L.marker([point.lat, point.lng], { icon: createIcon(color) });

            // Popup au clic
            const badgeColor = point.is_toxic ? "danger" : point.is_invasive ? "warning" : point.is_edible ? "success" : "info";
            const badgeText  = point.is_toxic ? "Toxique" : point.is_invasive ? "Invasive" : point.is_edible ? "Comestible" : "Médicinale";

            marker.bindPopup(`
                <div style="min-width:160px;">
                    <strong>${point.plant_name}</strong><br>
                    <em style="color:#6c757d; font-size:0.8rem;">${point.scientific}</em><br>
                    <span class="badge bg-${badgeColor} mt-1">${badgeText}</span><br>
                    <small style="color:#6c757d;"><i class="bi bi-calendar3"></i> ${point.date}</small><br>
                    <a href="/rapport?id=${point.id}" style="font-size:0.8rem;">Voir le rapport →</a>
                </div>
            `);

            marker.addTo(scanMap);
            bounds.push([point.lat, point.lng]);
        });

        // Ajuster le zoom pour voir tous les marqueurs
        if (bounds.length > 1) {
            scanMap.fitBounds(bounds, { padding: [30, 30] });
        } else if (bounds.length === 1) {
            scanMap.setView(bounds[0], 13);
        }

    } catch (error) {
        console.error("Erreur chargement carte:", error);
    }
}
