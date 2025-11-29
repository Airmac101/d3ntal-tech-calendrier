document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("eventModal");
    const closeBtn = document.querySelector(".close");
    const addBtn = document.getElementById("addEventBtn");

    const eventIdField = document.getElementById("eventId");
    const dateField = document.getElementById("eventDate");
    const typeField = document.getElementById("eventType");
    const titleField = document.getElementById("eventTitle");
    const collabField = document.getElementById("eventCollab");
    const notesField = document.getElementById("eventNotes");
    const priorityField = document.getElementById("eventPriority");

    const form = document.getElementById("eventForm");

    // ----------------------------
    // FONCTIONS
    // ----------------------------

    function openModal() {
        modal.style.display = "block";
    }

    function closeModal() {
        modal.style.display = "none";
        form.reset();
        eventIdField.value = "";
    }

    // OUVERTURE MODAL POUR CREATION
    addBtn.addEventListener("click", function () {
        document.getElementById("modalTitle").innerText = "Ajouter un événement";
        openModal();
    });

    // OUVERTURE MODAL LORS DU CLIC SUR UN JOUR
    document.querySelectorAll(".day-cell").forEach(cell => {
        cell.addEventListener("click", function (event) {

            // éviter d'ouvrir le modal si on clique sur un événement
            if (event.target.classList.contains("event-item")) return;

            const date = this.getAttribute("data-date").substring(0, 10);
            document.getElementById("modalTitle").innerText = "Ajouter un événement";

            eventIdField.value = "";
            dateField.value = date;
            typeField.value = "";
            titleField.value = "";
            collabField.value = "";
            notesField.value = "";
            priorityField.value = "normal";

            openModal();
        });
    });

    // OUVERTURE MODAL POUR EDITION D'UN EVENEMENT
    document.querySelectorAll(".event-item").forEach(item => {
        item.addEventListener("click", function (e) {
            e.stopPropagation();

            const id = this.getAttribute("data-event-id");

            fetch(`/get_event/${id}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById("modalTitle").innerText = "Modifier un événement";

                    eventIdField.value = data.id;
                    dateField.value = data.date;
                    typeField.value = data.type;
                    titleField.value = data.title;
                    collabField.value = data.collaborators;
                    notesField.value = data.notes;
                    priorityField.value = data.priority;

                    openModal();
                });
        });
    });

    // FERMETURE DU MODAL
    closeBtn.addEventListener("click", closeModal);

    window.addEventListener("click", function (event) {
        if (event.target === modal) closeModal();
    });

    // ENVOI DU FORMULAIRE
    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const payload = {
            id: eventIdField.value,
            date: dateField.value,
            type: typeField.value,
            title: titleField.value,
            collaborators: collabField.value,
            notes: notesField.value,
            priority: priorityField.value
        };

        fetch("/save_event", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(() => {
                location.reload();
            });

    });

});
