from flask import Flask

from config import Config
from database.db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def home():
    return "Smart Expense Tracker is running!"

@app.route("/test-db")
def test_db():
    try:
        connection = get_db_connection()

        if connection.is_connected():
            connection.close()
            return "Database connection successful!"

        return "Database connection failed."

    except Exception as error:
        return f"Database error: {error}"

if __name__ == "__main__":
    app.run(debug=True)