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


# ============================================================
# ADD TRANSACTION
# ============================================================

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

            flash(
                "Amount must be greater than zero.",
                "error"
            )

            return redirect(
                url_for("transactions.add_transaction")
            )

        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s
            AND type = %s
            """,
            (
                category_id,
                transaction_type
            )
        )

        category = cursor.fetchone()

        if not category:

            cursor.close()
            connection.close()

            flash(
                "Invalid category selected.",
                "error"
            )

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
            VALUES
            (%s, %s, %s, %s, %s, %s)
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

        flash(
            "Transaction added successfully.",
            "success"
        )

        return redirect(url_for("transactions.list_transactions"))


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


# ============================================================
# TRANSACTIONS LIST
# ============================================================

@transactions_bp.route("/")
def list_transactions():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    transaction_type = request.args.get(
        "type",
        ""
    ).strip()


    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    query = """
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
    """

    params = [session["user_id"]]


    # SEARCH

    if search:

        query += """
            AND (
                t.description LIKE %s
                OR c.name LIKE %s
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value
        ])


    # TYPE FILTER

    if transaction_type in ["Income", "Expense"]:

        query += """
            AND t.type = %s
        """

        params.append(transaction_type)


    query += """
        ORDER BY t.transaction_date DESC, t.id DESC
    """


    cursor.execute(
        query,
        tuple(params)
    )

    transactions = cursor.fetchall()


    # SUMMARY

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Income'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS total_income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Expense'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS total_expense

        FROM transactions

        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    summary = cursor.fetchone()


    cursor.close()
    connection.close()


    balance = (
        float(summary["total_income"])
        - float(summary["total_expense"])
    )


    return render_template(
        "transactions.html",
        transactions=transactions,
        search=search,
        transaction_type=transaction_type,
        total_income=summary["total_income"],
        total_expense=summary["total_expense"],
        balance=balance
    )


# ============================================================
# DELETE TRANSACTION
# ============================================================

@transactions_bp.route(
    "/delete/<int:transaction_id>",
    methods=["POST"]
)
def delete_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))


    connection = get_db_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM transactions
        WHERE id = %s
        AND user_id = %s
        """,
        (
            transaction_id,
            session["user_id"]
        )
    )


    connection.commit()


    deleted = cursor.rowcount


    cursor.close()
    connection.close()


    if deleted:

        flash(
            "Transaction deleted successfully.",
            "success"
        )

    else:

        flash(
            "Transaction not found.",
            "error"
        )


    return redirect(
        url_for("transactions.list_transactions")
    )