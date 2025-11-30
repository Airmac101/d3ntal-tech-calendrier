<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>D3NTAL TECH - Calendrier</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style_v2.css') }}">
</head>

<body>

    <!-- TOPBAR -->
           <div class="topbar">
                <div class="topbar-title">D3NTAL TECH</div>
                <a class="nav-btn" href="{{ url_for('export_today') }}" style="margin-right: 20px;">Export du jour</a>
                <a class="topbar-logout" href="/logout">Déconnexion</a>

    </div>

    <!-- CONTAINER -->
    <div class="container">

        <!-- NAVIGATION CALENDRIER -->
        <div class="calendar-nav">
            <a class="nav-btn" href="/calendar?year={{ prev_year }}&month={{ prev_month }}">← Mois précédent</a>

            <h2>{{ month_name }} {{ year }}</h2>

            <a class="nav-btn" href="/calendar?year={{ next_year }}&month={{ next_month }}">Mois suivant →</a>
        </div>

        <!-- BOUTON AJOUT -->
        <div class="add-wrapper">
            <a href="#" id="openModalBtn" class="nav-btn add-btn">
                + Ajouter un événement
            </a>
        </div>

        <!-- TABLE CALENDRIER -->
        <table class="calendar">
            <tr>
                <th>Lundi</th>
                <th>Mardi</th>
                <th>Mercredi</th>
                <th>Jeudi</th>
                <th>Vendredi</th>
                <th>Samedi</th>
                <th>Dimanche</th>
            </tr>

            {% for week in calendar_days %}
            <tr>
                {% for day in week %}
                {% set is_other = (day.month != month) %}
                {% set is_today = (day == current_day) %}
                {% set day_key = day.isoformat() %}
                {% set day_events = events_by_date.get(day_key, []) %}

                <td class="calendar-day{% if is_other %} other-month{% endif %}{% if is_today %} today{% endif %}"
                    data-date="{{ day_key }}">
                    <div class="day-number">{{ day.day }}</div>

                    {% for ev in day_events %}
                        {% set display_time = 'Journée entière' if ev.time == '00:00' else ev.time %}
                    <div class="event-badge event-type-{{ ev.css_class }}"
                         data-event-id="{{ ev.id }}"
                         data-event-title="{{ ev.title }}"
                         data-event-date="{{ ev.date }}"
                         data-event-time="{{ ev.time }}"
                         data-event-type="{{ ev.type }}"
                         data-event-priority="{{ ev.priority }}"
                         data-event-notes="{{ ev.notes }}"
                         data-event-collaborators="{{ ev.collaborators }}">
                        <div class="event-line">
                            <span class="event-time">{{ display_time }}</span>
                            <span class="event-title">{{ ev.title }}</span>
                        </div>
                        <div class="event-meta">
                            {{ ev.type }}
                            {% if ev.collaborators %}
                                — {{ ev.collaborators }}
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>

        <!-- RÉCAPITULATIF DU MOIS -->
        <div class="weekly-summary-box">
            <h3>Récapitulatif du mois :
                {{ week_start.strftime('%d/%m/%Y') }} → {{ week_end.strftime('%d/%m/%Y') }}
            </h3>

            <!-- BOUTON EXPORT RÉCAPITULATIF JOUR -->
            <div style="text-align: right; margin-bottom: 12px;">
                <a href="{{ url_for('export_today') }}" class="nav-btn">
                    Exporter le récapitulatif du jour
                </a>
            </div>

            <div class="weekly-summary-list">
                {% if week_summary|length == 0 %}
                    <div class="week-line">
                        <span class="week-none">Aucun événement enregistré pour ce mois en cours.</span>
                    </div>
                {% else %}
                    {% for day_key, d in week_summary.items()|sort(attribute='1.date') %}
                        <div class="week-line">
                            <span class="week-day">
                                {{ d.date.strftime('%A %d %B').capitalize() }} :
                            </span>

                            {% if d.events|length == 0 %}
                                <span class="week-none">—</span>
                            {% else %}
                                {% for ev in d.events %}
                                    {% set label_time = 'Journée entière' if ev.time == '00:00' else ev.time %}
                                    <span class="week-event">
                                        <span class="priority priority-{{ ev.priority|lower }}">
                                            [{{ ev.priority|upper }}]
                                        </span>
                                        {{ label_time }} — {{ ev.type }} — {{ ev.title }}
                                        {% if ev.collab %}
                                            ({{ ev.collab }})
                                        {% endif %}
                                        {% if ev.notes %}
                                            — <em>{{ ev.notes }}</em>
                                        {% endif %}
                                    </span>
                                    {% if not loop.last %} | {% endif %}
                                {% endfor %}
                            {% endif %}
                        </div>
                    {% endfor %}
                {% endif %}
            </div>
        </div>

    </div>
    <!-- MODALE AJOUT / EDIT -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal-box" id="modalBox">
            <span class="close-btn" id="closeModalBtn">&times;</span>
            <h3 id="modalTitle">Ajouter un événement</h3>

            <div id="errorMessageModal" class="error" style="display:none;"></div>

            <!-- TITRE -->
            <input id="eventTitle" type="text" placeholder="Titre de l’événement">

            <!-- DATE -->
            <input id="eventDate" type="date">

            <!-- HEURE -->
            <input id="eventTime" type="time">

            <!-- JOURNÉE ENTIÈRE -->
            <label style="margin-top:8px; display:block;">
                <input type="checkbox" id="allDayCheckbox">
                Journée entière (sans préciser d’heure)
            </label>

            <!-- TYPE -->
            <select id="eventType">
                <option value="Rendez-vous Client">Rendez-vous Client</option>
                <option value="Rendez-vous Fournisseur">Rendez-vous Fournisseur</option>
                <option value="Réunion interne">Réunion interne</option>
                <option value="Administration">Administration</option>
                <option value="Urgence cabinet">Urgence cabinet</option>
                <option value="Formation">Formation</option>
                <option value="Autre">Autre</option>
            </select>

            <input id="eventTypeCustom" type="text" placeholder="Précisez le type (Autre)" style="display:none;">

            <!-- COLLABORATEURS -->
            <div class="collab-title">Collaborateurs :</div>
            <div class="collab-group">
                <label><input type="checkbox" class="collab-checkbox" value="Denis"> Denis</label>
                <label><input type="checkbox" class="collab-checkbox" value="Isis"> Isis</label>
                <label><input type="checkbox" class="collab-checkbox" value="Assistante"> Assistante</label>
                <label><input type="checkbox" class="collab-checkbox" id="collabOtherCheckbox" value="__AUTRE__"> Autre</label>
            </div>

            <input id="eventCollaboratorsOther" type="text" placeholder="Autre collaborateur" style="display:none;">

            <!-- PRIORITÉ -->
            <select id="eventPriority">
                <option value="Normal" selected>Normal</option>
                <option value="Urgent">Urgent</option>
                <option value="Important">Important</option>
                <option value="Critique">Critique</option>
            </select>

            <!-- NOTES -->
            <textarea id="eventNotes" rows="6" placeholder="Informations supplémentaires..."
                class="notes-textarea"></textarea>

            <button id="saveEventBtn">Enregistrer</button>
            <button id="deleteEventBtn" class="delete-btn" style="display:none;">Supprimer</button>
        </div>
    </div>

    <!-- MENU CONTEXTUEL JOUR -->
    <div id="dayContextMenu" class="context-menu" style="display:none;"></div>

    <!-- SCRIPT -->
    <script>
        const modalOverlay = document.getElementById("modalOverlay");
        const modalBox = document.getElementById("modalBox");
        const openModalBtn = document.getElementById("openModalBtn");
        const closeModalBtn = document.getElementById("closeModalBtn");

        const titleInput = document.getElementById("eventTitle");
        const dateInput = document.getElementById("eventDate");
        const timeInput = document.getElementById("eventTime");
        const allDayCheckbox = document.getElementById("allDayCheckbox");

        const typeSelect = document.getElementById("eventType");
        const typeCustomInput = document.getElementById("eventTypeCustom");
        const prioritySelect = document.getElementById("eventPriority");
        const notesInput = document.getElementById("eventNotes");

        const collabOtherCheckbox = document.getElementById("collabOtherCheckbox");
        const collabOtherInput = document.getElementById("eventCollaboratorsOther");

        const saveBtn = document.getElementById("saveEventBtn");
        const deleteBtn = document.getElementById("deleteEventBtn");

        const contextMenu = document.getElementById("dayContextMenu");

        let editingEventId = null;

		/* Forcer le picker natif */
        if (dateInput && dateInput.showPicker) {
            dateInput.addEventListener("click", () => dateInput.showPicker());
        }
        if (timeInput && timeInput.showPicker) {
            timeInput.addEventListener("click", () => {
                if (!allDayCheckbox.checked) timeInput.showPicker();
            });
        }

        /* Journée entière → désactiver l’heure */
        allDayCheckbox.addEventListener("change", () => {
            if (allDayCheckbox.checked) {
                timeInput.disabled = true;
            } else {
                timeInput.disabled = false;
            }
        });

        function resetModal() {
            editingEventId = null;
            document.getElementById("modalTitle").innerText = "Ajouter un événement";
            saveBtn.textContent = "Enregistrer";
            deleteBtn.style.display = "none";

            titleInput.value = "";
            dateInput.value = "";
            timeInput.value = "";
            allDayCheckbox.checked = false;
            timeInput.disabled = false;

            typeSelect.value = "Rendez-vous Client";
            typeCustomInput.style.display = "none";
            typeCustomInput.value = "";

            prioritySelect.value = "Normal";
            notesInput.value = "";

            document.querySelectorAll(".collab-checkbox").forEach(cb => cb.checked = false);
            collabOtherCheckbox.checked = false;
            collabOtherInput.style.display = "none";
            collabOtherInput.value = "";
        }

        /* Ouvrir la modale avec position dynamique */
        function openModalAt(x, y) {
            modalOverlay.style.display = "block";

            const boxWidth = modalBox.offsetWidth;
            const boxHeight = modalBox.offsetHeight;

            let left = x;
            let top = y;

            /* Empêcher de sortir à droite */
            if (left + boxWidth > window.innerWidth - 20) {
                left = window.innerWidth - boxWidth - 20;
            }
            if (left < 20) left = 20;

            /* Empêcher de sortir en bas (TON OPTION A) */
            if (top + boxHeight > window.innerHeight - 20) {
                top = window.innerHeight - boxHeight - 20;
            }
            if (top < 20) top = 20;

            modalBox.style.position = "fixed";
            modalBox.style.left = left + "px";
            modalBox.style.top = top + "px";
        }

        function openAddEventModalForDate(dateStr, clickX, clickY) {
            resetModal();
            dateInput.value = dateStr || "";
            openModalAt(clickX, clickY);
        }
        function openEditModalFromBadge(badge, clickX, clickY) {
            editingEventId = badge.dataset.eventId;
            document.getElementById("modalTitle").innerText = "Modifier l’événement";
            saveBtn.textContent = "Mettre à jour";
            deleteBtn.style.display = "block";

            titleInput.value = badge.dataset.eventTitle || "";
            dateInput.value = badge.dataset.eventDate || "";
            timeInput.value = badge.dataset.eventTime || "";

            /* Journée entière */
            if ((badge.dataset.eventTime || "") === "00:00") {
                allDayCheckbox.checked = true;
                timeInput.disabled = true;
            } else {
                allDayCheckbox.checked = false;
                timeInput.disabled = false;
            }

            /* Type */
            const type = badge.dataset.eventType || "";
            const known = [
                "Rendez-vous Client",
                "Rendez-vous Fournisseur",
                "Réunion interne",
                "Administration",
                "Urgence cabinet",
                "Formation"
            ];
            if (known.includes(type)) {
                typeSelect.value = type;
                typeSelect.dispatchEvent(new Event("change"));
            } else {
                typeSelect.value = "Autre";
                typeSelect.dispatchEvent(new Event("change"));
                typeCustomInput.value = type;
            }

            /* Priorité */
            prioritySelect.value = badge.dataset.eventPriority || "Normal";

            /* Notes */
            notesInput.value = badge.dataset.eventNotes || "";

            /* Collaborateurs */
            document.querySelectorAll(".collab-checkbox").forEach(cb => cb.checked = false);
            collabOtherCheckbox.checked = false;
            collabOtherInput.style.display = "none";
            collabOtherInput.value = "";

            const raw = (badge.dataset.eventCollaborators || "").split(",").map(v => v.trim());
            let rest = [];

            raw.forEach(v => {
                const L = v.toLowerCase();
                if (L.includes("denis")) document.querySelector('input[value="Denis"]').checked = true;
                else if (L.includes("isis")) document.querySelector('input[value="Isis"]').checked = true;
                else if (L.includes("assist")) document.querySelector('input[value="Assistante"]').checked = true;
                else if (v) rest.push(v);
            });

            if (rest.length > 0) {
                collabOtherCheckbox.checked = true;
                collabOtherInput.style.display = "block";
                collabOtherInput.value = rest.join(", ");
            }

            openModalAt(clickX, clickY);
        }

        /* Bouton global Ajouter */
        openModalBtn.onclick = (e) => {
            e.preventDefault();
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 3;
            resetModal();
            openModalAt(centerX, centerY);
        };

        closeModalBtn.onclick = () => {
            modalOverlay.style.display = "none";
        };

        modalOverlay.onclick = (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.style.display = "none";
            }
        };

        /* Type = Autre → champ texte */
        typeSelect.onchange = () => {
            if (typeSelect.value === "Autre") {
                typeCustomInput.style.display = "block";
            } else {
                typeCustomInput.style.display = "none";
                typeCustomInput.value = "";
            }
        };

        /* Collaborateur Autre */
        collabOtherCheckbox.onchange = () => {
            collabOtherInput.style.display =
                collabOtherCheckbox.checked ? "block" : "none";
            if (!collabOtherCheckbox.checked)
                collabOtherInput.value = "";
        };

        /* Ancien comportement : clic sur badge = modifier */
        document.querySelectorAll(".event-badge").forEach(b => {
            b.onclick = (evt) => {
                evt.stopPropagation();
                const rect = b.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                openEditModalFromBadge(b, x, y);
            };
        });

        /* MENU CONTEXTUEL */
        function buildAndShowContextMenuForDayCell(td, clickX, clickY) {
            const dateStr = td.dataset.date;
            const badges = td.querySelectorAll(".event-badge");

            let html = "";
            html += `<div class="context-item" data-action="add" data-date="${dateStr}">➕ Ajouter un événement</div>`;

            badges.forEach(b => {
                const time = b.dataset.eventTime || "";
                const type = b.dataset.eventType || "";
                const title = b.dataset.eventTitle || "";
                const labelTime = (time === "00:00") ? "Journée entière" : time;
                const label = `✏️ Modifier : ${type} (${labelTime}) — ${title}`;
                html += `<div class="context-item" data-action="edit" data-event-id="${b.dataset.eventId}" data-date="${dateStr}">${label}</div>`;
            });

            contextMenu.innerHTML = html;
            contextMenu.style.display = "block";

            let left = clickX;
            let top = clickY;

            const menuWidth = 260;
            const menuHeight = 40 + 30 * badges.length;

            if (left + menuWidth > window.innerWidth - 10)
                left = window.innerWidth - menuWidth - 10;
            if (top + menuHeight > window.innerHeight - 10)
                top = window.innerHeight - menuHeight - 10;
            if (left < 10) left = 10;
            if (top < 10) top = 10;

            contextMenu.style.left = left + "px";
            contextMenu.style.top = top + "px";
        }

        /* Clic sur cellule → menu contextuel */
        document.querySelectorAll(".calendar-day").forEach(td => {
            td.addEventListener("click", (e) => {
                if (e.target.closest(".event-badge")) {
                    return;
                }
                e.stopPropagation();

                const rect = td.getBoundingClientRect();
                const x = e.clientX || (rect.left + rect.width / 2);
                const y = e.clientY || (rect.top + rect.height / 2);

                buildAndShowContextMenuForDayCell(td, x, y);
            });
        });

        /* Actions depuis le menu contextuel */
        contextMenu.addEventListener("click", (e) => {
            e.stopPropagation();
            const item = e.target.closest(".context-item");
            if (!item) return;

            const action = item.dataset.action;
            const dateStr = item.dataset.date;
            const eventId = item.dataset.eventId;

            const rect = contextMenu.getBoundingClientRect();
            const clickX = rect.left + rect.width / 2;
            const clickY = rect.top + rect.height / 2;

            contextMenu.style.display = "none";

            if (action === "add") {
                openAddEventModalForDate(dateStr, clickX, clickY);
            } else if (action === "edit") {
                const badge = document.querySelector(`.event-badge[data-event-id="${eventId}"]`);
                if (badge) {
                    openEditModalFromBadge(badge, clickX, clickY);
                }
            }
        });

        /* Fermer le menu contextuel en cliquant ailleurs */
        document.addEventListener("click", () => {
            contextMenu.style.display = "none";
        });

        /* Sauvegarde */
        saveBtn.onclick = async () => {
            let collaborators = [];
            document.querySelectorAll(".collab-checkbox").forEach(cb => {
                if (cb.checked && cb.value !== "__AUTRE__") collaborators.push(cb.value);
            });
            if (collabOtherCheckbox.checked && collabOtherInput.value.trim()) {
                collaborators.push(collabOtherInput.value.trim());
            }

            let eventType = typeSelect.value;
            if (eventType === "Autre") eventType = typeCustomInput.value.trim();

            let eventTimeValue = timeInput.value;
            if (allDayCheckbox.checked) eventTimeValue = "00:00";

            const payload = {
                title: titleInput.value.trim(),
                event_date: dateInput.value,
                event_time: eventTimeValue,
                event_type: eventType,
                collaborators: collaborators.join(", "),
                priority: prioritySelect.value,
                notes: notesInput.value.trim()
            };

            if (editingEventId) payload.event_id = editingEventId;

            const url = editingEventId ? "/api/update_event" : "/api/add_event";

            const res = await fetch(url, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.status === "success") {
                window.location.reload();
            } else {
                alert("Erreur lors de l’enregistrement.");
            }
        };

        /* Suppression */
        deleteBtn.onclick = async () => {
            if (!editingEventId) return;
            if (!confirm("Supprimer cet événement ?")) return;

            const res = await fetch("/api/delete_event", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ event_id: editingEventId })
            });

            const data = await res.json();
            if (data.status === "success") {
                window.location.reload();
            } else {
                alert("Erreur lors de la suppression.");
            }
        };

    </script>

</body>
</html>
