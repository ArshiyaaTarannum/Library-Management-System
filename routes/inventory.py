from flask import (
    Blueprint,
    render_template,
    request,
    url_for
)

from config import (
    INVENTORY_SORT_COLUMNS,
    VALID_STATUSES,
    VALID_CONDITIONS,
    BORROW_LIMIT
) 


from database import cur
inventory_bp=Blueprint("inventory", __name__)

def build_inventory_sort_links(current_sort, current_dir):


    links = {}

    for column in INVENTORY_SORT_COLUMNS:

        args = request.args.to_dict()

        if current_sort == column and current_dir == "asc":
            args["dir"] = "desc"
        else:
            args["dir"] = "asc"

        args["sort"] = column

        links[column] = url_for("inventory.inventory", **args)

    return links

@inventory_bp.route("/inventory")
def inventory():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")
    status_filter = request.args.get("status_filter", "").strip()
    condition_filter = request.args.get("condition_filter", "").strip()

    sort_by = request.args.get("sort", "copy_id")
    if sort_by not in INVENTORY_SORT_COLUMNS:
        sort_by = "copy_id"

    sort_dir = request.args.get("dir", "asc").lower()
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"


    cur.execute("""
        SELECT COUNT(*)
        FROM Book
    """)

    total_books = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
    """)

    total_copies = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Status='Available'
    """)

    available = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Status='Issued'
    """)

    issued = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Status='Damaged'
    """)

    damaged = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Status='Lost'
    """)

    lost = cur.fetchone()[0]


    query = """
        SELECT
            BookCopy.CopyID,
            BookCopy.BookID,
            Book.BookName,
            Category.CategoryName,
            BookCopy.Shelf,
            BookCopy.Status,
            BookCopy.`Condition`,
            BookCopy.AdditionalRemark,
            BookCopy.DateAdded

        FROM BookCopy

        JOIN Book
        ON BookCopy.BookID = Book.BookID

        JOIN Category
        ON Book.CategoryID = Category.CategoryID

        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "copy_id":
            query += " AND BookCopy.CopyID LIKE %s"

        elif search_by == "book_id":
            query += " AND BookCopy.BookID LIKE %s"

        elif search_by == "shelf":
            query += " AND BookCopy.Shelf LIKE %s"

        elif search_by == "status":
            query += " AND BookCopy.Status LIKE %s"

        else:
            query += " AND Book.BookName LIKE %s"

        values.append("%" + search + "%")

    if status_filter in VALID_STATUSES:
        query += " AND BookCopy.Status = %s"
        values.append(status_filter)

    if condition_filter in VALID_CONDITIONS:
        query += " AND BookCopy.`Condition` = %s"
        values.append(condition_filter)

    sort_column = INVENTORY_SORT_COLUMNS[sort_by]
    sql_dir = "DESC" if sort_dir == "desc" else "ASC"

    query += f" ORDER BY {sort_column} {sql_dir}"

    cur.execute(query, values)

    copies = cur.fetchall()

    # ---- Active members, with their current Issued count, for the ----
    # ---- Issue-book dropdown added to this page. Read-only display -  ----
    # ---- the actual borrow-limit enforcement still happens only      ----
    # ---- inside issue_book(), via get_active_issue_count().          ----

    active_members = get_active_members_with_issue_counts()

    return render_template(
        "inventory.html",
        total_books=total_books,
        total_copies=total_copies,
        available=available,
        issued=issued,
        damaged=damaged,
        lost=lost,
        copies=copies,
        showing_count=len(copies),
        search=search,
        search_by=search_by,
        status_filter=status_filter,
        condition_filter=condition_filter,
        valid_statuses=sorted(VALID_STATUSES),
        valid_conditions=sorted(VALID_CONDITIONS),
        sort_links=build_inventory_sort_links(sort_by, sort_dir),
        current_sort=sort_by,
        current_dir=sort_dir,
        active_members=active_members,
        borrow_limit=BORROW_LIMIT
    )
