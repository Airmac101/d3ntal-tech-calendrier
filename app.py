from flask import Flask, render_template, request, session, redirect, flash
import os

app = Flask(__name__)
app.secret_key = "cle_secrete_d3ntal_tech"

# Emails autorisés
AUTHORIZED_EMAILS = [
    "denismeuret01@gmail.com",
    "denismeuret@d3ntal-tech.fr",
    "isis.stouvenel@d3ntal-tech.fr"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")

        if email in AUTHORIZED_EMAILS:
            session["user"] = email
            return redirect("/calendar")  # ✅ REDIRECTION DIRECTE
        else:
            flash("❌ Email non autorisé. Accès refusé.")

    return render_template("login.html")


@app.route("/calendar")
def calendar():
    if "user" not in session:
        return redirect("/")
    return render_template("calendar.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
