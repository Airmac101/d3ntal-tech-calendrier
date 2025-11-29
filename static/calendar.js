// ===========================
//  VARIABLES DU MODAL
// ===========================
const modal = document.getElementById("eventModal");
const modalTitle = document.getElementById("modalTitle");
const closeModal = document.querySelector(".close");

const fieldId = document.getElementById("eventId");
const fieldDate = document.getElementById("eventDate");
const fieldType = document.getElementById("eventType");
const fieldTitle = document.getElementById("eventTitle");
const fieldCollab = document.getElementById("eventCollab");
const fieldNotes = document.getElementById("eventNotes");
const fieldPriority = document.getElementById("eventPriority");

const eventForm = document.getElementById("eventForm");


// ===========================
//  OUVERTURE MODAL (NOUVEL ÉVÉNEMENT)
// ===========================
function openCreateEvent(dateStr) {
    modalTitle.textContent = "Ajouter un événement";
    fieldId.value = "";
    fieldDate.value = dateStr;
    fieldType.value = "";
    fieldTitle.value = "";
    fieldCollab.value = "";
    fieldNotes.value = "";
    fieldPriority.value = "normal";

    modal.style.display = "block";
}


// ===========================
//  OUVERTURE MODAL (MODIFIER ÉVÉNEMENT)
// ===========================
function openEditEvent(eventId) {
    fetch(`/event/${eventId}`)
        .then(res => res.json())
        .then(data => {
            modalTitle.textContent = "Modifier l'événement";

            fieldId.value = data.id;
            fieldDate.value = data.date;
            fieldType.value = data.type;
            fieldTitle.value = data.title;
            fieldCollab.value = data.collaborators;
            fieldNotes.value = data.notes;
            fieldPriority.value = data.priority;

            modal.style.display = "block";
        });
}


// ===========================
//  FERMETURE DU MODAL
// ===========================
closeModal.onclick = () => modal.style.display = "none";

window.onclick = function (event) {
    if (event.target === modal) modal.style.display = "none";
};


// ===========================
//  CLIC SUR LES CASES DU CALENDRIER
// ===========================
document.querySelectorAll(".day-cell").forEach(cell => {
    cell.addEventListener("click", function (e) {
        // éviter que cliquer dans un événement ouvre un "create"
        if (e.target.classList.contains("event-item") ||
            e.target.parentNode.classList.contains("event-item")) {
            return;
        }

        const date = this.dataset.date;
        openCreateEvent(date);
    });
});


// ===========================
//  CLIC SUR UN ÉVÉNEMENT EXISTANT
// ===========================
document.querySelectorAll(".event-item").forEach(item => {
    item.addEventListener("click", function (e) {
        e.stopPropagation(); // empêche d'ouvrir create

        const eventId = this.dataset.eventId;
        openEditEvent(eventId);
    });
});


// ===========================
//  CLIC SUR LE BOUTON "AJOUTER"
// ===========================
const addEventBtn = document.getElementById("addEventBtn");
if (addEventBtn) {
    addEventBtn.addEventListener("click", () => {
        openCreateEvent("");
    });
}


// ===========================
//  SAUVEGARDE FORMULAIRE
// ===========================
eventForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const payload = {
        id: fieldId.value,
        date: fieldDate.value,
        type: fieldType.value,
        title: fieldTitle.value,
        collaborators: fieldCollab.value,
        notes: fieldNotes.value,
        priority: fieldPriority.value
    };

    fetch("/save_event", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                window.location.reload();
            } else {
                alert("Erreur lors de l’enregistrement.");
            }
        });
});

