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

        transaction_type = request.form.get("type", "").strip()
        category_id = request.form.get("category_id", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        transaction_date = request.form.get("transaction_date", "").strip()

        # -----------------------------
        # Validate transaction type
        # -----------------------------

        if transaction_type not in ["Income", "Expense"]:

            cursor.close()
            connection.close()

            flash("Invalid transaction type.", "error")

            return redirect(
                url_for("transactions.add_transaction")
            )


        # -----------------------------
        # Validate amount
        # -----------------------------

        try:

            amount_value = float(amount)

            if amount_value <= 0:
                raise ValueError

        except (ValueError, TypeError):

            cursor.close()
            connection.close()

            flash(
                "Amount must be a valid number greater than zero.",
                "error"
            )

            return redirect(
                url_for("transactions.add_transaction")
            )


        # -----------------------------
        # Validate category
        # -----------------------------

        try:

            category_id_value = int(category_id)

        except (ValueError, TypeError):

            cursor.close()
            connection.close()

            flash("Invalid category selected.", "error")

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
                category_id_value,
                transaction_type
            )
        )

        category = cursor.fetchone()


        if not category:

            cursor.close()
            connection.close()

            flash("Invalid category selected.", "error")

            return redirect(
                url_for("transactions.add_transaction")
            )


        # -----------------------------
        # Validate date
        # -----------------------------

        if not transaction_date:

            cursor.close()
            connection.close()

            flash("Transaction date is required.", "error")

            return redirect(
                url_for("transactions.add_transaction")
            )


        # -----------------------------
        # Insert transaction
        # -----------------------------

        try:

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
                    category_id_value,
                    amount_value,
                    transaction_type,
                    description,
                    transaction_date
                )
            )

            connection.commit()

        except Exception:

            connection.rollback()

            cursor.close()
            connection.close()

            flash(
                "Something went wrong while saving the transaction.",
                "error"
            )

            return redirect(
                url_for("transactions.add_transaction")
            )


        cursor.close()
        connection.close()

        flash(
            "Transaction added successfully.",
            "success"
        )

        return redirect(
            url_for("transactions.list_transactions")
        )


    # -----------------------------
    # Load categories
    # -----------------------------

    cursor.execute(
        """
        SELECT
            id,
            name,
            type

        FROM categories

        ORDER BY
            type,
            name
        """
    )

    categories = cursor.fetchall()

    cursor.close()
    connection.close()


    default_date = request.args.get("date", "")

    return render_template(
        "add_transaction.html",
        categories=categories,
        default_date=default_date
    )


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
    cursor = connection.cursor(dictionary=True)


    # -----------------------------
    # Transaction query
    # -----------------------------

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

    params = [
        session["user_id"]
    ]


    # Search filter

    if search:

        query += """
            AND (
                t.description LIKE %s
                OR c.name LIKE %s
            )
        """

        search_value = f"%{search}%"

        params.extend(
            [
                search_value,
                search_value
            ]
        )


    # Type filter

    if transaction_type in [
        "Income",
        "Expense"
    ]:

        query += """
            AND t.type = %s
        """

        params.append(
            transaction_type
        )


    query += """
        ORDER BY
            t.transaction_date DESC,
            t.id DESC
    """


    cursor.execute(
        query,
        tuple(params)
    )

    transactions = cursor.fetchall()


    # -----------------------------
    # Summary
    # -----------------------------

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
        (
            session["user_id"],
        )
    )


    summary = cursor.fetchone()


    total_income = float(
        summary["total_income"]
    )

    total_expense = float(
        summary["total_expense"]
    )

    balance = (
        total_income
        - total_expense
    )


    cursor.close()
    connection.close()


    return render_template(
        "transactions.html",

        transactions=transactions,

        search=search,

        transaction_type=transaction_type,

        total_income=total_income,

        total_expense=total_expense,

        balance=balance
    )


@transactions_bp.route(
    "/edit/<int:transaction_id>",
    methods=["GET", "POST"]
)
def edit_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # --------------------------------
    # Get existing transaction
    # --------------------------------

    cursor.execute(
        """
        SELECT
            id,
            category_id,
            amount,
            type,
            description,
            transaction_date

        FROM transactions

        WHERE id = %s
        AND user_id = %s
        """,
        (
            transaction_id,
            session["user_id"]
        )
    )

    transaction = cursor.fetchone()

    if not transaction:

        cursor.close()
        connection.close()

        flash(
            "Transaction not found.",
            "error"
        )

        return redirect(
            url_for("transactions.list_transactions")
        )


    # --------------------------------
    # Update transaction
    # --------------------------------

    if request.method == "POST":

        transaction_type = request.form.get(
            "type",
            ""
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        amount = request.form.get(
            "amount",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date = request.form.get(
            "transaction_date",
            ""
        ).strip()


        # Validate type

        if transaction_type not in [
            "Income",
            "Expense"
        ]:

            cursor.close()
            connection.close()

            flash(
                "Invalid transaction type.",
                "error"
            )

            return redirect(
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        # Validate amount

        try:

            amount_value = float(amount)

            if amount_value <= 0:
                raise ValueError

        except (ValueError, TypeError):

            cursor.close()
            connection.close()

            flash(
                "Amount must be a valid number greater than zero.",
                "error"
            )

            return redirect(
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        # Validate category

        try:

            category_id_value = int(category_id)

        except (ValueError, TypeError):

            cursor.close()
            connection.close()

            flash(
                "Invalid category selected.",
                "error"
            )

            return redirect(
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        cursor.execute(
            """
            SELECT id

            FROM categories

            WHERE id = %s
            AND type = %s
            """,
            (
                category_id_value,
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
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        # Validate date

        if not transaction_date:

            cursor.close()
            connection.close()

            flash(
                "Transaction date is required.",
                "error"
            )

            return redirect(
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        # --------------------------------
        # Update database
        # --------------------------------

        try:

            cursor.execute(
                """
                UPDATE transactions

                SET
                    category_id = %s,
                    amount = %s,
                    type = %s,
                    description = %s,
                    transaction_date = %s

                WHERE id = %s
                AND user_id = %s
                """,
                (
                    category_id_value,
                    amount_value,
                    transaction_type,
                    description,
                    transaction_date,
                    transaction_id,
                    session["user_id"]
                )
            )

            connection.commit()

        except Exception:

            connection.rollback()

            cursor.close()
            connection.close()

            flash(
                "Something went wrong while updating the transaction.",
                "error"
            )

            return redirect(
                url_for(
                    "transactions.edit_transaction",
                    transaction_id=transaction_id
                )
            )


        cursor.close()
        connection.close()

        flash(
            "Transaction updated successfully.",
            "success"
        )

        return redirect(
            url_for("transactions.list_transactions")
        )


    # --------------------------------
    # Load categories
    # --------------------------------

    cursor.execute(
        """
        SELECT
            id,
            name,
            type

        FROM categories

        ORDER BY
            type,
            name
        """
    )

    categories = cursor.fetchall()

    cursor.close()
    connection.close()


    return render_template(
        "edit_transaction.html",
        transaction=transaction,
        categories=categories
    )


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