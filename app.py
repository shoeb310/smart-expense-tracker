from flask import Flask, redirect, url_for, render_template, session

from config import Config
from routes.auth import auth_bp
from routes.transactions import transactions_bp

app = Flask(__name__)
app.config.from_object(Config)


app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)


@app.route("/")
def home():
    return redirect(url_for("auth.login"))


@app.route("/test-db")
def test_db():

    from database.db import get_db_connection

    try:

        connection = get_db_connection()

        if connection.is_connected():

            connection.close()

            return "Database connection successful!"

        return "Database connection failed."

    except Exception as error:

        return f"Database error: {error}"


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)