<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Accès D3NTAL TECH</title>
</head>
<body>

<h1>Accès sécurisé D3NTAL TECH</h1>

<form method="POST">
    <label>Veuillez entrer votre email :</label><br><br>
    <input type="email" name="email" required>
    <br><br>
    <button type="submit">Valider</button>
</form>

{% with messages = get_flashed_messages() %}
    {% if messages %}
        <ul>
        {% for message in messages %}
            <li style="color:red;">{{ message }}</li>
        {% endfor %}
        </ul>
    {% endif %}
{% endwith %}

</body>
</html>
