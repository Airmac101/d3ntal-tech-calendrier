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
    const deleteBtn = document.getElementById("deleteEventBtn"); // peut être null si pas encore dans le HTML

    // ----------------------------
    // FONCTIONS DE BASE
    // ----------------------------

    function openModal() {
        if (!modal) return;
        modal.style.display = "block";
    }

    function closeModal() {
        if (!modal) return;
        modal.style.display = "none";
        if (form) form.reset();
        if (eventIdField) eventIdField.value = "";
        if (deleteBtn) {
            deleteBtn.style.display = "none";
        }
    }

    // ----------------------------
    // OUVERTURE POUR CREATION
    // ----------------------------
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            const modalTitle = document.getElementById("modalTitle");
            if (modalTitle) modalTitle.innerText = "Ajouter un événement";

            if (eventIdField) eventIdField.value = "";
            if (dateField) dateField.value = "";
            if (typeField) typeField.value = "";
            if (titleField) titleField.value = "";
            if (collabField) collabField.value = "";
            if (notesField) notesField.value = "";
            if (priorityField) priorityField.value = "normal";

            if (deleteBtn) deleteBtn.style.display = "none";

            openModal();
        });
    }

    // ----------------------------
    // CLIC SUR UN JOUR → CREATION
    // ----------------------------
    document.querySelectorAll(".day-cell").forEach(function (cell) {
        cell.addEventListener("click", function (event) {

            // Ne pas ouvrir si on a cliqué sur un événement déjà existant
            if (event.target.classList.contains("event-item")) {
                return;
            }

            const dateAttr = this.getAttribute("data-date");
            const date = dateAttr ? dateAttr.substring(0, 10) : "";

            const modalTitle = document.getElementById("modalTitle");
            if (modalTitle) modalTitle.innerText = "Ajouter un événement";

            if (eventIdField) eventIdField.value = "";
            if (dateField) dateField.value = date;
            if (typeField) typeField.value = "";
            if (titleField) titleField.value = "";
            if (collabField) collabField.value = "";
            if (notesField) notesField.value = "";
            if (priorityField) priorityField.value = "normal";

            if (deleteBtn) deleteBtn.style.display = "none";

            openModal();
        });
    });

    // ----------------------------
    // CLIC SUR UN EVENEMENT → EDITION
    // ----------------------------
    document.querySelectorAll(".event-item").forEach(function (item) {
        item.addEventListener("click", function (e) {
            e.stopPropagation();

            const id = this.getAttribute("data-event-id");
            if (!id) return;

            fetch(`/event/${id}`)
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Erreur lors du chargement de l'événement");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.status === "error") {
                        throw new Error(data.message || "Erreur API");
                    }

                    const modalTitle = document.getElementById("modalTitle");
                    if (modalTitle) modalTitle.innerText = "Modifier un événement";

                    if (eventIdField) eventIdField.value = data.id || "";
                    if (dateField) dateField.value = data.date || "";
                    if (typeField) typeField.value = data.type || "";
                    if (titleField) titleField.value = data.title || "";
                    if (collabField) collabField.value = data.collaborators || "";
                    if (notesField) notesField.value = data.notes || "";
                    if (priorityField) {
                        priorityField.value = (data.priority || "normal").toLowerCase();
                    }

                    if (deleteBtn) {
                        deleteBtn.style.display = "inline-block";
                    }

                    openModal();
                })
                .catch(function (error) {
                    console.error(error);
                    alert("Impossible de charger cet événement.");
                });
        });
    });

    // ----------------------------
    // FERMETURE DU MODAL
    // ----------------------------
    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // ----------------------------
    // ENREGISTREMENT (CREATION / MODIF)
    // ----------------------------
    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const payload = {
                id: eventIdField ? eventIdField.value : "",
                date: dateField ? dateField.value : "",
                type: typeField ? typeField.value : "",
                title: titleField ? titleField.value : "",
                collaborators: collabField ? collabField.value : "",
                notes: notesField ? notesField.value : "",
                priority: priorityField ? priorityField.value : "normal"
            };

            fetch("/save_event", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Erreur lors de l'enregistrement");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.status !== "success") {
                        throw new Error(data.message || "Erreur lors de l'enregistrement");
                    }
                    location.reload();
                })
                .catch(function (error) {
                    console.error(error);
                    alert("Impossible d'enregistrer cet événement.");
                });
        });
    }

    // ----------------------------
    // SUPPRESSION DEPUIS LE MODAL
    // ----------------------------
    if (deleteBtn) {
        deleteBtn.addEventListener("click", function () {
            const id = eventIdField ? eventIdField.value : "";
            if (!id) {
                return;
            }

            const confirmDelete = window.confirm(
                "Supprimer définitivement cet événement ?"
            );
            if (!confirmDelete) return;

            fetch("/delete_event", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: id })
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Erreur lors de la suppression");
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (data.status !== "success") {
                        throw new Error(data.message || "Erreur lors de la suppression");
                    }
                    location.reload();
                })
                .catch(function (error) {
                    console.error(error);
                    alert("Impossible de supprimer cet événement.");
                });
        });
    }

});
