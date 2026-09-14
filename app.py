from flask import Flask, redirect, url_for, render_template, session

from config import Config
from routes.auth import auth_bp
from routes.transactions import transactions_bp
from routes.reports import reports_bp

app = Flask(__name__)
app.config.from_object(Config)


app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(reports_bp)


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

    from database.db import get_db_connection

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    user_id = session["user_id"]

    # -----------------------------
    # Get total income and expense
    # -----------------------------
    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Income' THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS total_income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Expense' THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS total_expense

        FROM transactions
        WHERE user_id = %s
        """,
        (user_id,)
    )

    summary = cursor.fetchone()

    total_income = float(summary["total_income"])
    total_expense = float(summary["total_expense"])
    balance = total_income - total_expense

    # -----------------------------
    # Calculate savings percentage
    # -----------------------------
    if total_income > 0:
        savings_percentage = (balance / total_income) * 100
    else:
        savings_percentage = 0

    # -----------------------------
    # Recent transactions
    # -----------------------------
    cursor.execute(
        """
        SELECT
            t.id,
            t.amount,
            t.type,
            t.description,
            t.transaction_date,
            c.name AS category

        FROM transactions t

        JOIN categories c
            ON t.category_id = c.id

        WHERE t.user_id = %s

        ORDER BY
            t.transaction_date DESC,
            t.id DESC

        LIMIT 5
        """,
        (user_id,)
    )

    recent_transactions = cursor.fetchall()

    # -----------------------------
    # Expense categories
    # -----------------------------
    cursor.execute(
        """
        SELECT
            c.name AS category,
            SUM(t.amount) AS total

        FROM transactions t

        JOIN categories c
            ON t.category_id = c.id

        WHERE
            t.user_id = %s
            AND t.type = 'Expense'

        GROUP BY c.id, c.name

        ORDER BY total DESC
        """,
        (user_id,)
    )

    expense_categories = cursor.fetchall()

    # -----------------------------
    # Monthly income vs expense
    # -----------------------------
    cursor.execute(
        """
        SELECT
            DATE_FORMAT(transaction_date, '%Y-%m') AS month,

            SUM(
                CASE
                    WHEN type = 'Income' THEN amount
                    ELSE 0
                END
            ) AS income,

            SUM(
                CASE
                    WHEN type = 'Expense' THEN amount
                    ELSE 0
                END
            ) AS expense

        FROM transactions

        WHERE user_id = %s

        GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')

        ORDER BY month
        """,
        (user_id,)
    )

    monthly_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        savings_percentage=savings_percentage,
        recent_transactions=recent_transactions,
        expense_categories=expense_categories,
        monthly_data=monthly_data
    )


if __name__ == "__main__":
    app.run(debug=True)