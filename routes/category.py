from flask import Blueprint, render_template, request, flash, redirect, url_for
import mysql.connector
from database import conn, cur

category_bp = Blueprint("category", __name__)

@category_bp.route("/category")
def category():

    search = request.args.get("search", "").strip()

    query = """
        SELECT CategoryID, CategoryName
        FROM Category
        WHERE 1=1
    """

    values = []

    if search:
        query += """
            AND (
                CategoryID LIKE %s
                OR CategoryName LIKE %s
            )
        """

        values.append("%" + search + "%")
        values.append("%" + search + "%")

    query += " ORDER BY CategoryID"

    cur.execute(query, values)
    categories = cur.fetchall()

    cur.execute("""
        SELECT CategoryID
        FROM Category
        ORDER BY CategoryID DESC
        LIMIT 1
    """)

    last_category = cur.fetchone()

    if last_category is None:
        next_category_id = "CAT001"
    else:
        number = int(last_category[0][3:]) + 1
        next_category_id = f"CAT{number:03d}"

    return render_template(
        "category.html",
        categories=categories,
        next_category_id=next_category_id
    )


@category_bp.route("/add_category", methods=["POST"])
def add_category():

    category_name = request.form["category_name"].strip().title()

    if not category_name:
        flash("Please enter a category name.")
        return redirect(url_for("category.category"))

    # Find the last category ID
    cur.execute("""
        SELECT CategoryID
        FROM Category
        ORDER BY CategoryID DESC
        LIMIT 1
    """)

    last_category = cur.fetchone()

    if last_category is None:
        category_id = "CAT001"
    else:
        number = int(last_category[0][3:])
        number += 1
        category_id = f"CAT{number:03d}"

    try:

        cur.execute("""
            INSERT INTO Category(CategoryID, CategoryName)
            VALUES(%s,%s)
        """, (category_id, category_name))

        conn.commit()

        flash("Category Added Successfully!")

    except mysql.connector.Error:

        flash("Category already exists!")

    return redirect(url_for("category.category"))

# DELETE CATEGORY


@category_bp.route("/delete_category/<category_id>")
def delete_category(category_id):

    try:

        cur.execute("""
            DELETE FROM Category
            WHERE CategoryID=%s
        """, (category_id,))

        conn.commit()

        flash("Category deleted successfully!")

    except mysql.connector.Error:

        flash("Cannot delete this category because books are assigned to it.")

    return redirect(url_for("category.category"))


@category_bp.route("/update_category", methods=["POST"])
def update_category():

    category_id = request.form["category_id"]
    category_name = request.form["category_name"].strip().title()

    if not category_name:

        flash("Category name cannot be empty.")

        return redirect(url_for("category.category"))

    cur.execute("""
        UPDATE Category
        SET CategoryName=%s
        WHERE CategoryID=%s
    """, (category_name, category_id))

    conn.commit()

    flash("Category Updated Successfully!")

    return redirect(url_for("categor.category"))
