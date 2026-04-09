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
let distributionChart = null;
let timelineChart     = null;
let topPlantsChart    = null;
let scanMap           = null;   // Instance Leaflet

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
 * Charger et afficher les alertes récentes.
 */
async function loadAlerts() {
    try {
        const data   = await apiGet("/api/analytics/alerts");
        const list   = document.getElementById("alertsList");
        const noAlert = document.getElementById("noAlerts");

        if (data.count === 0) {
            list.innerHTML = "";
            noAlert.classList.remove("d-none");
            return;
        }

        noAlert.classList.add("d-none");

        // Générer un item de liste pour chaque alerte
        list.innerHTML = data.alerts.map(alert => {
            // Choisir le style selon le type d'alerte
            const isInvasive = alert.alert_types.includes("Espèce invasive");
            const isToxic    = alert.alert_types.includes("Toxicité élevée");
            const itemClass  = isToxic ? "alert-item-toxic" : "alert-item-invasive";

            return `
                <a href="/rapport?id=${alert.scan_id}"
                   class="list-group-item list-group-item-action ${itemClass} py-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1 fw-semibold">${alert.plant_name}</h6>
                            <small class="text-muted fst-italic">${alert.scientific_name}</small>
                            <div class="mt-1">
                                ${alert.alert_types.map(type =>
                                    `<span class="badge ${type.includes("Toxicité") ? 'bg-danger' : 'bg-warning text-dark'} me-1">
                                        ${type}
                                    </span>`
                                ).join("")}
                            </div>
                        </div>
                        <small class="text-muted">${alert.date}</small>
                    </div>
                </a>
            `;
        }).join("");

    } catch (error) {
        console.error("Erreur chargement alertes:", error);
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
