// =========================================================
//  CALENDAR.JS — VERSION FINALE
// =========================================================

// ----- SELECTEURS -----
const modal = document.getElementById("eventModal");
const closeBtn = document.querySelector(".close");

const eventDate = document.getElementById("eventDate");
const eventTime = document.getElementById("eventTime");
const eventAllDay = document.getElementById("eventAllDay");
const eventType = document.getElementById("eventType");
const eventTitle = document.getElementById("eventTitle");
const eventCollab = document.getElementById("eventCollab");
const eventNotes = document.getElementById("eventNotes");
const eventPriority = document.getElementById("eventPriority");

const saveBtn = document.getElementById("saveBtn");
const deleteBtn = document.getElementById("deleteBtn");

const addEventBtn = document.getElementById("addEventBtn");

// Variables internes
let currentEventId = null;


// =========================================================
//  FONCTIONS UTILITAIRES
// =========================================================

function openModal() {
    modal.style.display = "flex";
}

function closeModal() {
    modal.style.display = "none";
    currentEventId = null;
    clearForm();
}

function clearForm() {
    eventDate.value = "";
    eventTime.value = "";
    eventAllDay.checked = false;
    eventType.value = "rdv";
    eventTitle.value = "";
    eventCollab.value = "";
    eventNotes.value = "";
    eventPriority.value = "normale";

    deleteBtn.style.display = "none";
}


// =========================================================
//  AJOUT D'ÉVÉNEMENT
// =========================================================

addEventBtn.addEventListener("click", () => {
    clearForm();
    currentEventId = null;

    // date du jour pré-remplie
    const today = new Date().toISOString().split("T")[0];
    eventDate.value = today;

    document.getElementById("modalTitle").textContent = "Nouvel évènement";

    openModal();
});


// =========================================================
//  CLIQUER SUR UN JOUR
// =========================================================

document.querySelectorAll(".day-cell").forEach(cell => {
    cell.addEventListener("click", (e) => {
        // Empêche d'interférer avec le clic sur un événement
        if (e.target.classList.contains("event-item")) return;

        clearForm();
        currentEventId = null;

        const clickedDate = cell.dataset.date;
        eventDate.value = clickedDate;

        document.getElementById("modalTitle").textContent = "Nouvel évènement";

        openModal();
    });
});


// =========================================================
//  CLIQUER SUR UN ÉVÉNEMENT → ÉDITION
// =========================================================

document.querySelectorAll(".event-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.stopPropagation(); // évite l'ouverture comme nouvel événement

        const eventId = item.dataset.eventId;
        currentEventId = eventId;

        fetch(`/event/${eventId}`)
            .then(res => res.json())
            .then(data => {
                eventDate.value = data.date;
                eventTime.value = data.time || "";
                eventAllDay.checked = data.all_day === 1;

                eventType.value = data.type.toLowerCase();
                eventTitle.value = data.title;
                eventCollab.value = data.collab || "";
                eventNotes.value = data.notes || "";
                eventPriority.value = data.priority || "normale";

                deleteBtn.style.display = "block";
                document.getElementById("modalTitle").textContent = "Modifier l'évènement";

                openModal();
            });
    });
});


// =========================================================
//  SAUVEGARDER (CREATE / UPDATE)
// =========================================================

saveBtn.addEventListener("click", () => {
    const payload = {
        id: currentEventId,
        date: eventDate.value,
        time: eventAllDay.checked ? "" : eventTime.value,
        all_day: eventAllDay.checked,
        type: eventType.value,
        title: eventTitle.value,
        collaborators: eventCollab.value,
        notes: eventNotes.value,
        priority: eventPriority.value
    };

    fetch("/save_event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(() => {
            closeModal();
            window.location.reload();
        });
});


// =========================================================
//  SUPPRESSION
// =========================================================

deleteBtn.addEventListener("click", () => {
    if (!currentEventId) return;

    fetch("/delete_event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: currentEventId })
    })
        .then(res => res.json())
        .then(() => {
            closeModal();
            window.location.reload();
        });
});


// =========================================================
//  FERMETURE MODAL
// =========================================================

closeBtn.addEventListener("click", closeModal);

window.onclick = function (event) {
    if (event.target === modal) {
        closeModal();
    }
};
