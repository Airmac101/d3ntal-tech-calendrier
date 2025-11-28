from flask import Flask, render_template, request, session, redirect, flash

app = Flask(__name__)
app.secret_key = "cle_secrete_d3ntal_tech"

# Emails autorisés
AUTHORIZED_EMAILS = [
    "denismeuret01@gmail.com",
    "denismeuret@d3ntal-tech.fr",
    "isis.stouvenel@d3ntal-tech.fr"
]

# Page d'accueil simple
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")

        if email in AUTHORIZED_EMAILS:
            session["user"] = email
            return redirect("/login_successful")
        else:
            flash("❌ Email non autorisé. Accès refusé.")

    return render_template("login.html")


@app.route("/login_successful")
def login_successful():
    if "user" not in session:
        return redirect("/")
    return render_template("login_successful.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
