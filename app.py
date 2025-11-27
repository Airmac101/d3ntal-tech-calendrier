@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")

        conn = get_db()
        cur = conn.cursor()

        # Check if email already exists
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        # Insert new user into the database
        cur.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, email, "default_password"))  # Password can be changed after registration
        conn.commit()
        conn.close()

        return redirect("/login?success=1")

    return render_template("register.html")
