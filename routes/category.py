from flask import Blueprint, render_template, request, flash, redirect, url_for
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