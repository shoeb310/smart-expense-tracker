from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database.db import get_db_connection


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


@reports_bp.route("/")
def reports():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # --------------------------------
    # Build date filter
    # --------------------------------

    date_condition = ""
    date_params = []

    if start_date:
        date_condition += " AND transaction_date >= %s"
        date_params.append(start_date)

    if end_date:
        date_condition += " AND transaction_date <= %s"
        date_params.append(end_date)

    # --------------------------------
    # Overall summary
    # --------------------------------

    cursor.execute(
        f"""
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
        {date_condition}
        """,
        [user_id] + date_params
    )

    summary = cursor.fetchone()

    total_income = float(summary["total_income"])
    total_expense = float(summary["total_expense"])
    balance = total_income - total_expense

    # --------------------------------
    # Expense by category
    # --------------------------------

    cursor.execute(
        f"""
        SELECT
            c.name AS category,
            SUM(t.amount) AS total

        FROM transactions t

        JOIN categories c
            ON t.category_id = c.id

        WHERE
            t.user_id = %s
            AND t.type = 'Expense'
            {date_condition}

        GROUP BY c.id, c.name

        ORDER BY total DESC
        """,
        [user_id] + date_params
    )

    category_data = cursor.fetchall()

    for item in category_data:
        item["total"] = float(item["total"])

    # --------------------------------
    # Monthly report
    # --------------------------------

    cursor.execute(
        f"""
        SELECT
            DATE_FORMAT(transaction_date, '%Y-%m') AS month,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Income' THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'Expense' THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS expense

        FROM transactions

        WHERE user_id = %s
        {date_condition}

        GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')

        ORDER BY month
        """,
        [user_id] + date_params
    )

    monthly_data = cursor.fetchall()

    for item in monthly_data:
        item["income"] = float(item["income"])
        item["expense"] = float(item["expense"])

    cursor.close()
    connection.close()

    return render_template(
        "reports.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        category_data=category_data,
        monthly_data=monthly_data,
        start_date=start_date,
        end_date=end_date
    )