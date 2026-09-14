from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database.db import get_db_connection


transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/transactions"
)


@transactions_bp.route("/add", methods=["GET", "POST"])
def add_transaction():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        transaction_type = request.form["type"]
        category_id = request.form["category_id"]
        amount = request.form["amount"]
        description = request.form["description"].strip()
        transaction_date = request.form["transaction_date"]

        if not amount or float(amount) <= 0:
            cursor.close()
            connection.close()

            flash("Amount must be greater than zero.", "error")

            return redirect(
                url_for("transactions.add_transaction")
            )

        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s AND type = %s
            """,
            (category_id, transaction_type)
        )

        category = cursor.fetchone()

        if not category:
            cursor.close()
            connection.close()

            flash("Invalid category selected.", "error")

            return redirect(
                url_for("transactions.add_transaction")
            )

        cursor.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                category_id,
                amount,
                type,
                description,
                transaction_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                category_id,
                amount,
                transaction_type,
                description,
                transaction_date
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash("Transaction added successfully.", "success")

        return redirect(url_for("dashboard"))


    cursor.execute(
        """
        SELECT id, name, type
        FROM categories
        ORDER BY type, name
        """
    )

    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "add_transaction.html",
        categories=categories
    )