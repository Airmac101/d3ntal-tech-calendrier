// =========================================================
//  D3NTAL TECH - CALENDAR.JS (VERSION FINALE)
//  Compatible avec calendar.html + app.py actuels
// =========================================================

// --------- Sélecteurs principaux ---------
const modalOverlay = document.getElementById("modalOverlay");
const modalBox = document.getElementById("modalBox");
const closeModalBtn = document.getElementById("closeModalBtn");

const modalTitle = document.getElementById("modalTitle");
const errorMessageModal = document.getElementById("errorMessageModal");

const eventTitleInput = document.getElementById("eventTitle");
const eventDateInput = document.getElementById("eventDate");
const eventTimeInput = document.getElementById("eventTime");
const allDayCheckbox = document.getElementById("allDayCheckbox");

const eventTypeSelect = document.getElementById("eventType");
const eventTypeCustomInput = document.getElementById("eventTypeCustom");

const collabCheckboxes = document.querySelectorAll(".collab-checkbox");
const collabOtherCheckbox = document.getElementById("collabOtherCheckbox");
const eventCollaboratorsOtherInput = document.getElementById("eventCollaboratorsOther");

const eventPrioritySelect = document.getElementById("eventPriority");
const eventNotesTextarea = document.getElementById("eventNotes");

const existingFilesContainer = document.getElementById("existingFilesContainer");
const eventFilesInput = document.getElementById("eventFiles");

const saveEventBtn = document.getElementById("saveEventBtn");
const deleteEventBtn = document.getElementById("deleteEventBtn");

const openModalBtn = document.getElementById("openModalBtn");

const dayCells = document.querySelectorAll(".calendar-day");
const eventBadges = document.querySelectorAll(".event-badge");

const dayContextMenu = document.getElementById("dayContextMenu");

// --------- Variable globale pour suivre l'événement courant ---------
let currentEventId = null;
let currentEventFiles = []; // liste des fichiers existants (pour affichage)

// ====================================================================
//  UTILITAIRES
// ====================================================================

function openModal() {
    modalOverlay.style.display = "flex";
}

function closeModal() {
    modalOverlay.style.display = "none";
    currentEventId = null;
    currentEventFiles = [];
    clearForm();
}

function clearForm() {
    errorMessageModal.style.display = "none";
    errorMessageModal.textContent = "";

    eventTitleInput.value = "";
    eventDateInput.value = "";
    eventTimeInput.value = "";
    allDayCheckbox.checked = false;
    eventTimeInput.disabled = false;

    // Type
    eventTypeSelect.value = "Rendez-vous Client";
    eventTypeCustomInput.value = "";
    eventTypeCustomInput.style.display = "none";

    // Collaborateurs
    collabCheckboxes.forEach(cb => {
        cb.checked = false;
    });
    eventCollaboratorsOtherInput.value = "";
    eventCollaboratorsOtherInput.style.display = "none";

    // Priorité & notes
    eventPrioritySelect.value = "Normal";
    eventNotesTextarea.value = "";

    // Fichiers existants
    existingFilesContainer.innerHTML = "";
    existingFilesContainer.style.display = "none";

    // Fichiers à uploader
    if (eventFilesInput) {
        eventFilesInput.value = "";
    }

    deleteEventBtn.style.display = "none";
    modalTitle.textContent = "Ajouter un événement";
}

// Retourne la date du jour au format YYYY-MM-DD
function getTodayISO() {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

// Construit la chaîne "collaborators" à partir des checkboxes + champ Autre
function buildCollaboratorsString() {
    const parts = [];

    collabCheckboxes.forEach(cb => {
        if (!cb.checked) return;

        const val = cb.value;
        if (val === "__AUTRE__") {
            const otherVal = (eventCollaboratorsOtherInput.value || "").trim();
            if (otherVal) {
                parts.push(otherVal);
            }
        } else {
            parts.push(val);
        }
    });

    return parts.join(", ");
}

// Coche les cases à partir d’une chaîne "Denis, Isis, Autre..."
function setCollaboratorsFromString(collabString) {
    collabCheckboxes.forEach(cb => {
        cb.checked = false;
    });
    eventCollaboratorsOtherInput.value = "";
    eventCollaboratorsOtherInput.style.display = "none";

    if (!collabString) return;

    const rawList = collabString
        .split(",")
        .map(s => s.trim())
        .filter(s => s.length > 0);

    if (rawList.length === 0) return;

    const knownValues = ["Denis", "Isis", "Assistante"];

    const remaining = [];

    rawList.forEach(val => {
        if (knownValues.includes(val)) {
            const cb = Array.from(collabCheckboxes).find(c => c.value === val);
            if (cb) cb.checked = true;
        } else {
            remaining.push(val);
        }
    });

    if (remaining.length > 0) {
        if (collabOtherCheckbox) collabOtherCheckbox.checked = true;
        eventCollaboratorsOtherInput.value = remaining.join(", ");
        eventCollaboratorsOtherInput.style.display = "block";
    }
}

// Gère le champ "Autre type"
function syncTypeCustomField() {
    if (eventTypeSelect.value === "Autre") {
        eventTypeCustomInput.style.display = "block";
    } else {
        eventTypeCustomInput.style.display = "none";
        eventTypeCustomInput.value = "";
    }
}

// Applique le type (si non présent dans la liste, basculer sur Autre)
function setEventTypeFromValue(typeValue) {
    const optionsValues = Array.from(eventTypeSelect.options).map(o => o.value);
    if (optionsValues.includes(typeValue)) {
        eventTypeSelect.value = typeValue;
        eventTypeCustomInput.value = "";
        eventTypeCustomInput.style.display = "none";
        return;
    }

    // Type inconnu -> "Autre" + champ custom
    eventTypeSelect.value = "Autre";
    eventTypeCustomInput.value = typeValue || "";
    eventTypeCustomInput.style.display = "block";
}

// Gère la logique "journée entière"
function applyAllDayFromTime(timeStr) {
    if (!timeStr || timeStr === "00:00") {
        allDayCheckbox.checked = true;
        eventTimeInput.value = "";
        eventTimeInput.disabled = true;
    } else {
        allDayCheckbox.checked = false;
        eventTimeInput.disabled = false;
        eventTimeInput.value = timeStr;
    }
}

// Affiche les fichiers existants dans la modale
function renderExistingFiles(filesJsonStr) {
    existingFilesContainer.innerHTML = "";
    existingFilesContainer.style.display = "none";
    currentEventFiles = [];

    if (!filesJsonStr) return;

    let filesList = [];
    try {
        filesList = JSON.parse(filesJsonStr);
        if (!Array.isArray(filesList)) {
            filesList = [];
        }
    } catch (e) {
        filesList = [];
    }

    if (filesList.length === 0) return;

    currentEventFiles = filesList.slice();

    existingFilesContainer.style.display = "block";

    filesList.forEach(relPath => {
        const item = document.createElement("div");
        item.className = "file-item";

        const link = document.createElement("a");
        link.className = "file-item-link";
        link.href = `/download_file/${encodeURIComponent(relPath)}`;
        link.textContent = relPath.split("/").pop();

        item.appendChild(link);
        existingFilesContainer.appendChild(item);
    });
}

// Affiche un message d'erreur dans la modale
function showError(msg) {
    errorMessageModal.textContent = msg;
    errorMessageModal.style.display = "block";
}

// ====================================================================
//  OUVERTURE DE LA MODALE - AJOUT
// ====================================================================

if (openModalBtn) {
    openModalBtn.addEventListener("click", function (e) {
        e.preventDefault();
        clearForm();
        currentEventId = null;
        eventDateInput.value = getTodayISO();
        modalTitle.textContent = "Ajouter un événement";
        openModal();
    });
}

// Clic sur une cellule de jour vide -> création sur ce jour
dayCells.forEach(cell => {
    cell.addEventListener("click", function (e) {
        // Si on clique sur un badge d'événement à l'intérieur, laisser l'autre handler gérer
        if (e.target.closest(".event-badge")) {
            return;
        }

        clearForm();
        currentEventId = null;

        const dateStr = cell.dataset.date;
        if (dateStr) {
            eventDateInput.value = dateStr;
        } else {
            eventDateInput.value = getTodayISO();
        }

        modalTitle.textContent = "Ajouter un événement";
        openModal();
    });

    // Clic droit -> menu contextuel simple "Ajouter un événement"
    cell.addEventListener("contextmenu", function (e) {
        e.preventDefault();
        const dateStr = cell.dataset.date || getTodayISO();
        openDayContextMenu(e.clientX, e.clientY, dateStr);
    });
});

// ====================================================================
//  OUVERTURE DE LA MODALE - EDITION D'UN ÉVÉNEMENT EXISTANT
// ====================================================================

eventBadges.forEach(badge => {
    badge.addEventListener("click", function (e) {
        e.stopPropagation(); // ne pas déclencher le handler du jour

        clearForm();

        const eventId = badge.dataset.eventId;
        currentEventId = eventId || null;

        const title = badge.dataset.eventTitle || "";
        const dateStr = badge.dataset.eventDate || "";
        const timeStr = badge.dataset.eventTime || "";
        const typeStr = badge.dataset.eventType || "";
        const priorityStr = badge.dataset.eventPriority || "Normal";
        const notesStr = badge.dataset.eventNotes || "";
        const collabStr = badge.dataset.eventCollaborators || "";
        const filesJsonStr = badge.dataset.eventFiles || "";

        eventTitleInput.value = title;
        eventDateInput.value = dateStr;

        applyAllDayFromTime(timeStr);
        setEventTypeFromValue(typeStr);
        setCollaboratorsFromString(collabStr);

        eventPrioritySelect.value = priorityStr || "Normal";
        eventNotesTextarea.value = notesStr || "";

        renderExistingFiles(filesJsonStr);

        deleteEventBtn.style.display = "block";
        modalTitle.textContent = "Modifier l'événement";
        openModal();
    });
});

// ====================================================================
//  CONTEXT MENU JOUR (clic droit)
// ====================================================================

function openDayContextMenu(x, y, dateStr) {
    if (!dayContextMenu) return;

    dayContextMenu.innerHTML = "";

    const title = document.createElement("div");
    title.className = "context-title";
    title.textContent = dateStr;
    dayContextMenu.appendChild(title);

    const addItem = document.createElement("div");
    addItem.className = "context-item";
    addItem.textContent = "Ajouter un événement ce jour";
    addItem.addEventListener("click", () => {
        dayContextMenu.style.display = "none";
        clearForm();
        currentEventId = null;
        eventDateInput.value = dateStr;
        modalTitle.textContent = "Ajouter un événement";
        openModal();
    });
    dayContextMenu.appendChild(addItem);

    dayContextMenu.style.display = "block";
    dayContextMenu.style.left = x + "px";
    dayContextMenu.style.top = y + "px";
}

window.addEventListener("click", function (e) {
    if (dayContextMenu && e.target !== dayContextMenu && !dayContextMenu.contains(e.target)) {
        dayContextMenu.style.display = "none";
    }
});

// ====================================================================
//  GESTION DES CHAMPS SPÉCIAUX (All day / Autre type / Autre collab)
// ====================================================================

// Bascule journée entière
if (allDayCheckbox && eventTimeInput) {
    allDayCheckbox.addEventListener("change", function () {
        if (allDayCheckbox.checked) {
            eventTimeInput.value = "";
            eventTimeInput.disabled = true;
        } else {
            eventTimeInput.disabled = false;
        }
    });
}

// Type "Autre"
if (eventTypeSelect) {
    eventTypeSelect.addEventListener("change", syncTypeCustomField);
}

// Collaborateur "Autre"
if (collabOtherCheckbox && eventCollaboratorsOtherInput) {
    collabOtherCheckbox.addEventListener("change", function () {
        if (collabOtherCheckbox.checked) {
            eventCollaboratorsOtherInput.style.display = "block";
        } else {
            eventCollaboratorsOtherInput.style.display = "none";
            eventCollaboratorsOtherInput.value = "";
        }
    });
}

// ====================================================================
//  SAUVEGARDE (ADD / UPDATE)
// ====================================================================

if (saveEventBtn) {
    saveEventBtn.addEventListener("click", function () {
        errorMessageModal.style.display = "none";
        errorMessageModal.textContent = "";

        const title = (eventTitleInput.value || "").trim();
        const eventDateStr = (eventDateInput.value || "").trim();

        if (!title) {
            showError("Le titre est obligatoire.");
            return;
        }
        if (!eventDateStr) {
            showError("La date est obligatoire.");
            return;
        }

        // Gestion heure
        let eventTimeStr = (eventTimeInput.value || "").trim();
        if (allDayCheckbox.checked || !eventTimeStr) {
            eventTimeStr = "00:00";
        }

        // Gestion type (Autre + custom)
        let eventTypeStr = eventTypeSelect.value;
        if (eventTypeStr === "Autre") {
            const custom = (eventTypeCustomInput.value || "").trim();
            if (custom) {
                eventTypeStr = custom;
            } else {
                eventTypeStr = "Autre";
            }
        }

        const collaboratorsStr = buildCollaboratorsString();
        const priorityStr = eventPrioritySelect.value || "Normal";
        const notesStr = eventNotesTextarea.value || "";

        const payload = {
            title: title,
            event_date: eventDateStr,
            event_time: eventTimeStr,
            event_type: eventTypeStr,
            collaborators: collaboratorsStr,
            priority: priorityStr,
            notes: notesStr
        };

        let url = "/api/add_event";

        if (currentEventId) {
            url = "/api/update_event";
            payload.event_id = currentEventId;
        }

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                if (!data || data.status !== "success") {
                    showError("Erreur lors de l'enregistrement de l'événement.");
                    return;
                }

                const eventId = currentEventId || data.event_id;

                // S'il n'y a pas de nouveaux fichiers -> rechargement direct
                if (!eventFilesInput || !eventFilesInput.files || eventFilesInput.files.length === 0 || !eventId) {
                    closeModal();
                    window.location.reload();
                    return;
                }

                // Upload des fichiers
                const formData = new FormData();
                formData.append("event_id", eventId);

                Array.from(eventFilesInput.files).forEach(file => {
                    formData.append("files", file);
                });

                fetch("/upload_files", {
                    method: "POST",
                    body: formData
                })
                    .then(res => res.json())
                    .then(uploadData => {
                        if (!uploadData || uploadData.status !== "success") {
                            // On ne bloque pas si l'upload échoue, mais on informe
                            console.warn("Erreur lors de l'upload des fichiers.");
                        }
                        closeModal();
                        window.location.reload();
                    })
                    .catch(err => {
                        console.error("Upload error:", err);
                        closeModal();
                        window.location.reload();
                    });
            })
            .catch(err => {
                console.error("Save event error:", err);
                showError("Erreur réseau lors de l'enregistrement.");
            });
    });
}

// ====================================================================
//  SUPPRESSION
// ====================================================================

if (deleteEventBtn) {
    deleteEventBtn.addEventListener("click", function () {
        if (!currentEventId) return;

        const ok = window.confirm("Voulez-vous vraiment supprimer cet événement ?");
        if (!ok) return;

        fetch("/api/delete_event", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ event_id: currentEventId })
        })
            .then(res => res.json())
            .then(data => {
                if (!data || data.status !== "success") {
                    showError("Erreur lors de la suppression de l'événement.");
                    return;
                }
                closeModal();
                window.location.reload();
            })
            .catch(err => {
                console.error("Delete event error:", err);
                showError("Erreur réseau lors de la suppression.");
            });
    });
}

// ====================================================================
//  FERMETURE DE LA MODALE
// ====================================================================

if (closeModalBtn) {
    closeModalBtn.addEventListener("click", function () {
        closeModal();
    });
}

if (modalOverlay) {
    modalOverlay.addEventListener("click", function (e) {
        if (e.target === modalOverlay) {
            closeModal();
        }
    });
}
