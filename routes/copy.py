from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

import mysql.connector

from database import conn, cur

from config import (
    VALID_STATUSES,
    VALID_CONDITIONS,
    COPY_AVAILABLE,
    COPY_DAMAGED,
    COPY_LOST,
)

copies_bp = Blueprint("copies", __name__)

@copies_bp.route("/update_copy", methods=["POST"])
def update_copy():

    copy_id = request.form["copy_id"]
    shelf = request.form["shelf"]
    status = request.form["status"]
    condition = request.form["condition"]
    remark = request.form["remark"].strip()

    if status not in VALID_STATUSES:
        flash("Invalid status.")
        return redirect(url_for("inventory.inventory"))

    if condition not in VALID_CONDITIONS:
        flash("Invalid condition.")
        return redirect(url_for("inventory.inventory"))

    # Check copy exists and get current shelf

    cur.execute("""
        SELECT Shelf
        FROM BookCopy
        WHERE CopyID=%s
    """, (copy_id,))

    row = cur.fetchone()

    if row is None:
        flash("Copy not found.")
        return redirect(url_for("inventory.inventory"))

    old_shelf = row[0]

    # Check destination shelf exists

    cur.execute("""
        SELECT Capacity
        FROM Shelf
        WHERE ShelfID=%s
    """, (shelf,))

    row = cur.fetchone()

    if row is None:
        flash("Invalid shelf.")
        return redirect(url_for("inventory.inventory"))

    capacity = row[0]

    # Check shelf capacity only if moving to another shelf

    if old_shelf != shelf:

        cur.execute("""
            SELECT COUNT(*)
            FROM BookCopy
            WHERE Shelf=%s
        """, (shelf,))

        used = cur.fetchone()[0]

        if used >= capacity:
            flash("Selected shelf is already full.")
            return redirect(url_for("inventory.inventory"))

    try:

        cur.execute("""
            UPDATE BookCopy
            SET
                Shelf=%s,
                Status=%s,
                Condition`=%s,
                AdditionalRemark=%s
            WHERE CopyID=%s
        """, (
            shelf,
            status,
            condition,
            remark,
            copy_id
        ))
        if cur.rowcount == 0:
            conn.rollback()
            flash("Copy not found.")
            return redirect(url_for("inventory.inventory"))

        conn.commit()

        flash("Copy updated successfully!")


    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to update copy.")

    return redirect(url_for("inventory.inventory"))

@copies_bp.route("/delete_copy/<copy_id>", methods=["POST"])
def delete_copy(copy_id):

    try:
        cur.execute("""
            DELETE FROM BookCopy
            WHERE CopyID=%s
        """, (copy_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Copy not found.")
            return redirect(url_for("inventory.inventory"))

        conn.commit()
        flash("Copy deleted successfully!")

    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to delete copy.")

    return redirect(url_for("inventory.inventory"))
