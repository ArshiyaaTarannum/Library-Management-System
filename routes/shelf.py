from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from config import VALID_SHELF_STATUS
import mysql.connector

from database import conn, cur
from helpers.book_helper import get_next_shelf_id

shelf_bp= Blueprint("shelf",__name__)
next_shelf_id = get_next_shelf_id()
shelf_id = get_next_shelf_id()

@shelf_bp.route("/shelf")
def shelf():

    search = request.args.get("search", "").strip()

    query = """
        SELECT
            ShelfID,
            ShelfName,
            Location,
            Capacity,
            Status
        FROM Shelf
        WHERE 1=1
    """

    values = []

    if search:

        query += """
            AND (
                ShelfID LIKE %s
                OR ShelfName LIKE %s
                OR Location LIKE %s
            )
        """

        values.append("%" + search + "%")
        values.append("%" + search + "%")
        values.append("%" + search + "%")

    query += " ORDER BY ShelfID"

    cur.execute(query, values)

    shelves = cur.fetchall()

    # Generate next Shelf ID

    cur.execute("""
        SELECT ShelfID
        FROM Shelf
        ORDER BY ShelfID DESC
        LIMIT 1
    """)

    last_shelf = cur.fetchone()

    if last_shelf is None:
        next_shelf_id = "SH001"
    else:
        number = int(last_shelf[0][2:]) + 1
        next_shelf_id = f"SH{number:03d}"

    return render_template(
        "shelf.html",
        shelves=shelves,
        next_shelf_id=next_shelf_id
    )

@shelf_bp.route("/add_shelf", methods=["POST"])
def add_shelf():

    shelf_name = request.form["shelf_name"].strip()
    location = request.form["location"].strip()

    try:
        capacity = int(request.form["capacity"])
    except ValueError:
        flash("Invalid shelf capacity.")
        return redirect(url_for("shelf.shelf"))

    status = request.form["status"]

    if status not in VALID_SHELF_STATUS:
        flash("Invalid shelf status.")
        return redirect(url_for("shelf.shelf"))

    if not shelf_name:
        flash("Shelf name is required.")
        return redirect(url_for("shelf.shelf"))

    if capacity < 1:
        flash("Shelf capacity must be at least 1.")
        return redirect(url_for("shelf.shelf"))

    # Check duplicate shelf name

    cur.execute("""
        SELECT 1
        FROM Shelf
        WHERE ShelfName=%s
    """, (shelf_name,))

    if cur.fetchone():
        flash("Shelf name already exists.")
        return redirect(url_for("shelf.shelf"))

    # Generate Shelf ID

    cur.execute("""
        SELECT ShelfID
        FROM Shelf
        ORDER BY ShelfID DESC
        LIMIT 1
    """)

    last = cur.fetchone()

    if last is None:
        shelf_id = "SH001"
    else:
        number = int(last[0][2:]) + 1
        shelf_id = f"SH{number:03d}"

    try:

        cur.execute("""
            INSERT INTO Shelf
            (
                ShelfID,
                ShelfName,
                Location,
                Capacity,
                Status
            )
            VALUES
            (%s,%s,%s,%s,%s)
        """,
                    (
                        shelf_id,
                        shelf_name,
                        location,
                        capacity,
                        status
                    ))

        conn.commit()

        flash("Shelf added successfully!")

    except mysql.connector.Error:

        conn.rollback()
        flash("Unable to add shelf.")

    return redirect(url_for("shelf.shelf"))

@shelf_bp.route("/update_shelf", methods=["POST"])
def update_shelf():

    shelf_id = request.form["shelf_id"]
    shelf_name = request.form["shelf_name"].strip()
    location = request.form["location"].strip()

    try:
        capacity = int(request.form["capacity"])
    except ValueError:
        flash("Invalid shelf capacity.")
        return redirect(url_for("shelf.shelf"))

    status = request.form["status"]

    if status not in VALID_SHELF_STATUS:
        flash("Invalid shelf status.")
        return redirect(url_for("shelf.shelf"))

    if capacity < 1:
        flash("Shelf capacity must be at least 1.")
        return redirect(url_for("shelf.shelf"))

    # Prevent duplicate names

    cur.execute("""
        SELECT ShelfID
        FROM Shelf
        WHERE ShelfName=%s
        AND ShelfID<>%s
    """, (shelf_name, shelf_id))

    if cur.fetchone():
        flash("Shelf name already exists.")
        return redirect(url_for("shelf.shelf"))

    # Don't allow capacity smaller than books already stored

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Shelf=%s
    """, (shelf_id,))

    used = cur.fetchone()[0]

    if capacity < used:
        flash(f"This shelf already contains {used} books.")
        return redirect(url_for("shelf.shelf"))

    try:
        cur.execute("""
            UPDATE Shelf
            SET
                ShelfName=%s,
                Location=%s,
                Capacity=%s,
                Status=%s
            WHERE ShelfID=%s
        """,
                    (
                        shelf_name,
                        location,
                        capacity,
                        status,
                        shelf_id
                    ))

        conn.commit()

        flash("Shelf updated successfully!")

    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to update shelf.")

    return redirect(url_for("shelf.shelf"))

@shelf_bp.route("/delete_shelf/<shelf_id>", methods=["POST"])
def delete_shelf(shelf_id):

    try:

        cur.execute("""
        DELETE FROM Shelf
        WHERE ShelfID=%s
        """,(shelf_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Shelf not found.")
            return redirect(url_for("shelf.shelf"))

        conn.commit()

        flash("Shelf deleted successfully!")

    except mysql.connector.Error:

        conn.rollback()

        flash("Shelf contains books and cannot be deleted.")

    return redirect(url_for("shelf"))
