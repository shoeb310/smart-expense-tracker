import csv
import io
import json
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor.execute(
        "SELECT COUNT(*) AS total_tx FROM transactions WHERE user_id = %s",
        (user_id,)
    )
    stats = cursor.fetchone()
    total_tx = stats["total_tx"] if stats else 0

    cursor.close()
    connection.close()

    currency = session.get("currency", "₹")
    monthly_budget = session.get("monthly_budget", 25000.0)

    return render_template(
        "settings.html",
        user=user,
        total_tx=total_tx,
        currency=currency,
        monthly_budget=monthly_budget,
        active_page="settings"
    )


@settings_bp.route("/profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("settings.index"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check for email collision
    cursor.execute(
        "SELECT id FROM users WHERE email = %s AND id != %s",
        (email, user_id)
    )
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        connection.close()
        flash("This email is already taken by another account.", "error")
        return redirect(url_for("settings.index"))

    cursor.execute(
        "UPDATE users SET name = %s, email = %s WHERE id = %s",
        (name, email, user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

    session["user_name"] = name
    session["user_email"] = email

    flash("Profile updated successfully!", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for("settings.index"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "error")
        return redirect(url_for("settings.index"))

    if new_password != confirm_password:
        flash("New password and confirmation do not match.", "error")
        return redirect(url_for("settings.index"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT password_hash FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], current_password):
        cursor.close()
        connection.close()
        flash("Current password is incorrect.", "error")
        return redirect(url_for("settings.index"))

    new_hash = generate_password_hash(new_password)
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (new_hash, user_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

    flash("Password changed successfully!", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/preferences", methods=["POST"])
def update_preferences():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    currency = request.form.get("currency", "₹").strip()
    budget_raw = request.form.get("monthly_budget", "25000").strip()

    try:
        budget = float(budget_raw)
        if budget < 0:
            budget = 0.0
    except ValueError:
        budget = 25000.0

    session["currency"] = currency
    session["monthly_budget"] = budget

    flash("Preferences saved successfully!", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/export/csv")
def export_csv():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            t.transaction_date AS date,
            t.type,
            c.name AS category,
            t.amount,
            t.description
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC, t.id DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Amount", "Description"])

    for row in rows:
        writer.writerow([
            str(row["date"]),
            row["type"],
            row["category"],
            f"{row['amount']:.2f}",
            row["description"] or ""
        ])

    csv_data = output.getvalue()
    filename = f"spendly_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@settings_bp.route("/export/json")
def export_json():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            t.id,
            t.transaction_date AS date,
            t.type,
            c.name AS category,
            t.amount,
            t.description
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC, t.id DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    for r in rows:
        r["date"] = str(r["date"])
        r["amount"] = float(r["amount"])

    payload = {
        "app": "Spendly Smart Expense Tracker",
        "exported_at": datetime.now().isoformat(),
        "total_transactions": len(rows),
        "transactions": rows
    }

    filename = f"spendly_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        json.dumps(payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@settings_bp.route("/reset", methods=["POST"])
def reset_data():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    password = request.form.get("confirm_password_reset", "")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT password_hash FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        cursor.close()
        connection.close()
        flash("Incorrect password. Reset cancelled.", "error")
        return redirect(url_for("settings.index"))

    cursor.execute(
        "DELETE FROM transactions WHERE user_id = %s",
        (user_id,)
    )
    connection.commit()
    cursor.close()
    connection.close()

    flash("All transactions have been wiped successfully.", "success")
    return redirect(url_for("settings.index"))
