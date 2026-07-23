from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import date, timedelta
import json
import mysql.connector
from routes.category import category_bp
from database import conn, cur

from routes.policy import policy_bp
app = Flask(__name__)
app.secret_key = "library_management_secret"
app.register_blueprint(category_bp)
app.register_blueprint(policy_bp)

VALID_STATUSES = {"Available", "Issued", "Damaged", "Lost"}
VALID_CONDITIONS = {"Excellent", "Good", "Fair", "Worn", "Damaged", "Other"}
VALID_SHELF_STATUS = {"Active", "Inactive"}

VALID_PAYMENT_MODES = {"Cash", "UPI", "Card"}
INVENTORY_SORT_COLUMNS = {
    "copy_id": "BookCopy.CopyID",
    "book_id": "BookCopy.BookID",
    "book_name": "Book.BookName",
    "category": "Category.CategoryName",
    "shelf": "BookCopy.Shelf",
    "status": "BookCopy.Status",
    "condition": "BookCopy.`Condition`",
    "date_added": "BookCopy.DateAdded",
}

BORROW_SORT_COLUMNS = {
    "transaction_id": "IssueTransaction.TransactionID",
    "copy_id": "IssueTransaction.CopyID",
    "book_id": "BookCopy.BookID",
    "book_name": "Book.BookName",
    "member_id": "Member.MemberID",
    "member_name": "Member.MemberName",
    "issue_date": "IssueTransaction.IssueDate",
    "due_date": "IssueTransaction.DueDate",
    "status": "IssueTransaction.Status",
    "fine": "IssueTransaction.FineAmount",
    "payment_status": "IssueTransaction.PaymentStatus",
}
# ---------------- LIBRARY SETTINGS ----------------

BORROW_LIMIT = 5

LOAN_PERIOD_DAYS = 14

FINE_BASE_RATE = 5                 # ₹5/day for first month
FINE_RATE_STEP = 5                 # Increase by ₹5/day every 30 days
FINE_MONTH_LENGTH_DAYS = 30
FINE_CAP_BUFFER = 100              # Maximum fine = Purchase Price + ₹100

# DASHBOARD PAGE 

@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/delete_book/<book_id>")
def delete_book(book_id):

    try:

        cur.execute("""
            DELETE FROM Book
            WHERE BookID=%s
        """, (book_id,))

        conn.commit()

        flash("Book deleted successfully!")

    except mysql.connector.Error:

        flash("Unable to delete the book.")

    return redirect(url_for("add_books"))

@app.route("/update_book", methods=["POST"])
def update_book():

    book_id = request.form["book_id"]
    book_name = request.form["book_name"].strip().title()
    author = request.form["author"].strip().title()
    category_id = request.form["category_id"]
    publication = request.form["publication"].strip().title()
    publication_date = request.form["publication_date"]
    entry_date = request.form["entry_date"]
    language = request.form["language"].strip().title()
    edition = request.form["edition"].strip()
    purchase_price = request.form["purchase_price"]

    if (
        not book_name
        or not author
        or not category_id
        or not publication
        or not publication_date
        or not entry_date
        or not language
        or not edition
        or not purchase_price
    ):

        flash("Please fill all fields.")
        return redirect(url_for("add_books"))

    cur.execute("""
        UPDATE Book
        SET
            BookName=%s,
            Author=%s,
            CategoryID=%s,
            Publication=%s,
            PublicationDate=%s,
            EntryDate=%s,
            Language=%s,
            Edition=%s,
            PurchasePrice=%s
        WHERE BookID=%s
    """, (
        book_name,
        author,
        category_id,
        publication,
        publication_date,
        entry_date,
        language,
        edition,
        purchase_price,
        book_id
    ))
    conn.commit()

    flash("Book Updated Successfully!")

    return redirect(url_for("add_books"))

# ADD BOOK PAGE

@app.route("/add_books")
def add_books():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    # ---------- Categories ----------

    cur.execute("""
        SELECT CategoryID, CategoryName
        FROM Category
        ORDER BY CategoryName
    """)

    categories = cur.fetchall()

    # ---------- Shelves ----------

    cur.execute("""
        SELECT ShelfID, ShelfName
        FROM Shelf
        WHERE Status='Active'
        ORDER BY ShelfName
    """)

    shelves = cur.fetchall()

    # ---------- Next Book ID ----------

    cur.execute("""
        SELECT BookID
        FROM Book
        ORDER BY BookID DESC
        LIMIT 1
    """)

    last_book = cur.fetchone()

    if last_book is None:
        next_book_id = "LIB0001"
    else:
        number = int(last_book[0][3:]) + 1
        next_book_id = f"LIB{number:04d}"

    query = """
        SELECT
            Book.BookID,
            Book.BookName,
            Book.Author,
            Category.CategoryName,
            Book.CategoryID,
            Book.Publication,
            Book.PublicationDate,
            Book.EntryDate,
            Book.Language,
            Book.Edition,
            COUNT(BookCopy.CopyID),
            Book.PurchasePrice

        FROM Book

        JOIN Category
        ON Book.CategoryID = Category.CategoryID

        LEFT JOIN BookCopy
        ON Book.BookID = BookCopy.BookID

        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "book_id":
            query += " AND Book.BookID LIKE %s"

        elif search_by == "author":
            query += " AND Book.Author LIKE %s"

        elif search_by == "publication":
            query += " AND Book.Publication LIKE %s"

        elif search_by == "category":
            query += " AND Category.CategoryName LIKE %s"

        else:
            query += " AND Book.BookName LIKE %s"

        values.append("%" + search + "%")

    query += """
        GROUP BY
        Book.BookID,
        Book.BookName,
        Book.Author,
        Category.CategoryName,
        Book.CategoryID,
        Book.Publication,
        Book.PublicationDate,
        Book.EntryDate,
        Book.Language,
        Book.Edition,
        Book.PurchasePrice

        ORDER BY Book.BookID
    """

    cur.execute(query, values)

    books = cur.fetchall()

    return render_template(
        "add_books.html",
        categories=categories,
        shelves=shelves,
        next_book_id=next_book_id,
        books=books,
        today=date.today().isoformat(),
        total_books=len(books)
    )

@app.route("/add_book", methods=["POST"])
def add_book():

    book_name = request.form["book_name"].strip().title()
    author = request.form["author"].strip().title()
    category_id = request.form["category_id"]
    publication = request.form["publication"].strip().title()
    publication_date = request.form["publication_date"]
    entry_date = request.form["entry_date"]
    language = request.form["language"].strip().title()
    edition = request.form["edition"].strip()
    try:
        total_copies = int(request.form["total_copies"])
    except (ValueError, TypeError):
        flash("Invalid Total Copies.")
        return redirect(url_for("add_books"))

    purchase_price = request.form["purchase_price"]
    copy_groups_raw = request.form.get("copy_groups", "")

    if (
        not book_name or
        not author or
        not category_id or
        not publication or
        not publication_date or
        not language or
        not edition or
        total_copies < 1
    ):

        flash("Please fill all required fields.")
        return redirect(url_for("add_books"))

    try:
        copy_groups = json.loads(copy_groups_raw)
    except (json.JSONDecodeError, TypeError):
        flash("Copy allocation data was missing or invalid. Please try again.")
        return redirect(url_for("add_books"))

    if not isinstance(copy_groups, list) or not copy_groups:
        flash("Please provide at least one copy allocation group.")
        return redirect(url_for("add_books"))

    cleaned_groups = []
    allocated = 0

    for group in copy_groups:

        if not isinstance(group, dict):
            flash("Copy allocation data was malformed. Please try again.")
            return redirect(url_for("add_books"))

        try:
            quantity = int(group.get("quantity", 0))
        except (TypeError, ValueError):
            flash("Every group needs a valid whole number of copies.")
            return redirect(url_for("add_books"))

        shelf = str(group.get("shelf", "")).strip()
        status = "Available"
        condition = str(group.get("condition", "")).strip()
        remark = str(group.get("remark", "")).strip()

        if quantity < 1:
            flash("Every group must contain at least 1 copy.")
            return redirect(url_for("add_books"))

        if not shelf:
            flash("Every group needs a Shelf.")
            return redirect(url_for("add_books"))

        if status not in VALID_STATUSES:
            flash("Every group needs a valid Status.")
            return redirect(url_for("add_books"))

        if condition not in VALID_CONDITIONS:
            flash("Every group needs a valid Condition.")
            return redirect(url_for("add_books"))
        cur.execute("""
            SELECT Capacity
            FROM Shelf
            WHERE ShelfID=%s
        """, (shelf,))

        row = cur.fetchone()

        if row is None:
            flash("Selected shelf does not exist.")
            return redirect(url_for("add_books"))

        capacity = row[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM BookCopy
            WHERE Shelf=%s
        """, (shelf,))

        current_books = cur.fetchone()[0]

        if current_books + quantity > capacity:

            flash(
                f"{shelf} only has "
                f"{capacity-current_books} spaces remaining."
            )

            return redirect(url_for("add_books"))

        cleaned_groups.append(
            (quantity, shelf, "Available", condition, remark))
        allocated += quantity

    if allocated != total_copies:
        flash(
            f"Allocated copies ({allocated}) do not match "
            f"Total Copies ({total_copies})."
        )
        return redirect(url_for("add_books"))

    try:

        # Generate Book ID

        cur.execute("""
            SELECT BookID
            FROM Book
            ORDER BY BookID DESC
            LIMIT 1
        """)

        last_book = cur.fetchone()

        if last_book is None:

            book_id = "LIB0001"

        else:

            number = int(last_book[0][3:]) + 1
            book_id = f"LIB{number:04d}"

        # Insert Book Master Record

        cur.execute("""
            INSERT INTO Book
            (
                BookID,
                BookName,
                Author,
                CategoryID,
                Publication,
                PublicationDate,
                EntryDate,
                Language,
                Edition,
                PurchasePrice
            )

            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )

        """,
                    (
                        book_id,
                        book_name,
                        author,
                        category_id,
                        publication,
                        publication_date,
                        entry_date,
                        language,
                        edition,
                        purchase_price
                    ))

        cur.execute("""
            SELECT CopyID
            FROM BookCopy
            ORDER BY CopyID DESC
            LIMIT 1
        """)

        last_copy = cur.fetchone()
        next_copy_number = 1 if last_copy is None else int(
            last_copy[0][2:]) + 1

        copy_rows = []

        for quantity, shelf, status, condition, remark in cleaned_groups:

            for _ in range(quantity):

                copy_id = f"CP{next_copy_number:06d}"
                next_copy_number += 1

                copy_rows.append((
                    copy_id,
                    book_id,
                    shelf,
                    status,
                    condition,
                    remark,
                    entry_date
                ))

        cur.executemany("""
            INSERT INTO BookCopy
            (
                CopyID,
                BookID,
                Shelf,
                Status,
                `Condition`,
                AdditionalRemark,
                DateAdded
            )

            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s
            )

        """, copy_rows)

        conn.commit()

        flash(
            f"Book Added Successfully with {total_copies} copies!"
        )

    except mysql.connector.Error as e:

        conn.rollback()

        print(e)

        flash("Unable to add book.")

    return redirect(url_for("add_books"))

@app.route("/books")
def books():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    query = """
        SELECT
            Book.BookID,
            Book.BookName,
            Book.Author,
            Category.CategoryName,
            Book.Publication,
            Book.PublicationDate,
            Book.EntryDate,
            Book.Language,
            Book.Edition,
            COUNT(BookCopy.CopyID),
            Book.PurchasePrice
        FROM Book

        JOIN Category
        ON Book.CategoryID = Category.CategoryID

        LEFT JOIN BookCopy
        ON Book.BookID = BookCopy.BookID

        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "book_id":
            query += " AND Book.BookID LIKE %s"

        elif search_by == "author":
            query += " AND Book.Author LIKE %s"

        elif search_by == "publication":
            query += " AND Book.Publication LIKE %s"

        elif search_by == "category":
            query += " AND Category.CategoryName LIKE %s"

        else:
            query += " AND Book.BookName LIKE %s"

        values.append("%" + search + "%")

    query += """
    GROUP BY
    Book.BookID,
    Book.BookName,
    Book.Author,
    Category.CategoryName,
    Book.Publication,
    Book.PublicationDate,
    Book.EntryDate,
    Book.Language,
    Book.Edition,
    Book.PurchasePrice

    ORDER BY Book.BookID
    """

    cur.execute(query, values)

    books = cur.fetchall()

    return render_template(
        "view_books.html",
        books=books
    )

def build_inventory_sort_links(current_sort, current_dir):


    links = {}

    for column in INVENTORY_SORT_COLUMNS:

        args = request.args.to_dict()

        if current_sort == column and current_dir == "asc":
            args["dir"] = "desc"
        else:
            args["dir"] = "asc"

        args["sort"] = column

        links[column] = url_for("inventory", **args)

    return links

@app.route("/update_copy", methods=["POST"])
def update_copy():

    copy_id = request.form["copy_id"]
    shelf = request.form["shelf"]
    status = request.form["status"]
    condition = request.form["condition"]
    remark = request.form["remark"].strip()

    if status not in VALID_STATUSES:
        flash("Invalid status.")
        return redirect(url_for("inventory"))

    if condition not in VALID_CONDITIONS:
        flash("Invalid condition.")
        return redirect(url_for("inventory"))

    # Check copy exists and get current shelf

    cur.execute("""
        SELECT Shelf
        FROM BookCopy
        WHERE CopyID=%s
    """, (copy_id,))

    row = cur.fetchone()

    if row is None:
        flash("Copy not found.")
        return redirect(url_for("inventory"))

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
        return redirect(url_for("inventory"))

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
            return redirect(url_for("inventory"))

    try:

        cur.execute("""
            UPDATE BookCopy
            SET
                Shelf=%s,
                Status=%s,
                `Condition`=%s,
                AdditionalRemark=%s
            WHERE CopyID=%s
        """, (
            shelf,
            status,
            condition,
            remark,
            copy_id
        ))

        conn.commit()

        flash("Copy updated successfully!")

    except mysql.connector.Error:

        conn.rollback()
        flash("Unable to update copy.")

    return redirect(url_for("inventory"))

@app.route("/delete_copy/<copy_id>")
def delete_copy(copy_id):

    try:

        cur.execute("""
            DELETE FROM BookCopy
            WHERE CopyID=%s
        """, (copy_id,))

        conn.commit()

        flash("Copy deleted successfully!")

    except mysql.connector.Error:

        conn.rollback()

        flash("Unable to delete copy.")

    return redirect(url_for("inventory"))

@app.route("/view_categories")
def view_categories():

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

    return render_template(
        "view_categories.html",
        categories=categories
    )

@app.route("/shelf")
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

@app.route("/add_shelf", methods=["POST"])
def add_shelf():

    shelf_name = request.form["shelf_name"].strip()
    location = request.form["location"].strip()

    try:
        capacity = int(request.form["capacity"])
    except ValueError:
        flash("Invalid shelf capacity.")
        return redirect(url_for("shelf"))

    status = request.form["status"]

    if status not in VALID_SHELF_STATUS:
        flash("Invalid shelf status.")
        return redirect(url_for("shelf"))

    if not shelf_name:
        flash("Shelf name is required.")
        return redirect(url_for("shelf"))

    if capacity < 1:
        flash("Shelf capacity must be at least 1.")
        return redirect(url_for("shelf"))

    # Check duplicate shelf name

    cur.execute("""
        SELECT 1
        FROM Shelf
        WHERE ShelfName=%s
    """, (shelf_name,))

    if cur.fetchone():
        flash("Shelf name already exists.")
        return redirect(url_for("shelf"))

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

    return redirect(url_for("shelf"))

@app.route("/update_shelf", methods=["POST"])
def update_shelf():

    shelf_id = request.form["shelf_id"]
    shelf_name = request.form["shelf_name"].strip()
    location = request.form["location"].strip()

    try:
        capacity = int(request.form["capacity"])
    except ValueError:
        flash("Invalid shelf capacity.")
        return redirect(url_for("shelf"))

    status = request.form["status"]

    if status not in VALID_SHELF_STATUS:
        flash("Invalid shelf status.")
        return redirect(url_for("shelf"))

    if capacity < 1:
        flash("Shelf capacity must be at least 1.")
        return redirect(url_for("shelf"))

    # Prevent duplicate names

    cur.execute("""
        SELECT ShelfID
        FROM Shelf
        WHERE ShelfName=%s
        AND ShelfID<>%s
    """, (shelf_name, shelf_id))

    if cur.fetchone():
        flash("Shelf name already exists.")
        return redirect(url_for("shelf"))

    # Don't allow capacity smaller than books already stored

    cur.execute("""
        SELECT COUNT(*)
        FROM BookCopy
        WHERE Shelf=%s
    """, (shelf_id,))

    used = cur.fetchone()[0]

    if capacity < used:
        flash(f"This shelf already contains {used} books.")
        return redirect(url_for("shelf"))

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

    return redirect(url_for("shelf"))

@app.route("/delete_shelf/<shelf_id>")
def delete_shelf(shelf_id):

    try:

        cur.execute("""
            DELETE FROM Shelf
            WHERE ShelfID=%s
        """, (shelf_id,))

        conn.commit()

        flash("Shelf deleted successfully!")

    except mysql.connector.Error:

        conn.rollback()

        flash("Shelf contains books and cannot be deleted.")

    return redirect(url_for("shelf"))

def generate_member_id():

    cur.execute("""
        SELECT MemberID
        FROM Member
        ORDER BY MemberID DESC
        LIMIT 1
    """)

    last_member = cur.fetchone()

    if last_member is None:
        return "MEM0001"

    number = int(last_member[0][3:]) + 1
    return f"MEM{number:04d}"

def generate_transaction_id():

    cur.execute("""
        SELECT TransactionID
        FROM IssueTransaction
        ORDER BY TransactionID DESC
        LIMIT 1
    """)

    last_transaction = cur.fetchone()

    if last_transaction is None:
        return "TXN000001"

    number = int(last_transaction[0][3:]) + 1
    return f"TXN{number:06d}"

def generate_payment_id():

    cur.execute("""
        SELECT PaymentID
        FROM FinePayment
        ORDER BY PaymentID DESC
        LIMIT 1
    """)

    last_payment = cur.fetchone()

    if last_payment is None:
        return "PAY000001"

    number = int(last_payment[0][3:]) + 1
    return f"PAY{number:06d}"

def get_active_issue_count(member_id):

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE MemberID=%s AND Status='Issued'
    """, (member_id,))

    return cur.fetchone()[0]

def get_overdue_days(due_date, as_of_date=None):

    as_of_date = as_of_date or date.today()

    if isinstance(due_date, str):
        due_date = date.fromisoformat(due_date)

    delta_days = (as_of_date - due_date).days

    return max(delta_days, 0)

def calculate_fine(due_date, return_date, purchase_price):

    overdue_days = get_overdue_days(due_date, return_date)

    if overdue_days == 0:
        return 0.0

    fine = 0.0
    remaining_days = overdue_days
    month_number = 1

    while remaining_days > 0:

        days_in_this_block = min(FINE_MONTH_LENGTH_DAYS, remaining_days)
        rate_for_this_block = FINE_BASE_RATE + \
            (FINE_RATE_STEP * (month_number - 1))

        fine += days_in_this_block * rate_for_this_block

        remaining_days -= days_in_this_block
        month_number += 1

    cap = float(purchase_price or 0) + FINE_CAP_BUFFER

    return round(min(fine, cap), 2)

@app.route("/inventory")
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

@app.route("/borrow_books")
def borrow_books():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")
    status_filter = request.args.get("status_filter", "").strip()
    payment_filter = request.args.get("payment_filter", "").strip()
    overdue_only = request.args.get("overdue_only", "") == "1"

    sort_by = request.args.get("sort", "issue_date")
    if sort_by not in BORROW_SORT_COLUMNS:
        sort_by = "issue_date"

    sort_dir = request.args.get("dir", "desc").lower()
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    today = date.today()

    # ---- Dashboard stats ----

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Issued'
    """)

    total_issued = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Issued' AND DueDate < %s
    """, (today.isoformat(),))

    total_overdue = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Returned' AND ActualReturnDate = %s
    """, (today.isoformat(),))

    returned_today = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(FineAmount), 0)
        FROM IssueTransaction
        WHERE Status='Returned' AND PaymentStatus='Pending'
    """)

    outstanding_fine = cur.fetchone()[0]


    active_members = get_active_members_with_issue_counts()
    available_copies = get_available_copies_for_issue()

    # ---- Borrowed Books table ----

    query = """
        SELECT
            IssueTransaction.TransactionID,
            IssueTransaction.CopyID,
            BookCopy.BookID,
            Book.BookName,
            Member.MemberID,
            Member.MemberName,
            IssueTransaction.IssueDate,
            IssueTransaction.DueDate,
            IssueTransaction.ActualReturnDate,
            IssueTransaction.Status,
            IssueTransaction.FineAmount,
            IssueTransaction.PaymentStatus,
            Book.PurchasePrice

        FROM IssueTransaction

        JOIN BookCopy
        ON IssueTransaction.CopyID = BookCopy.CopyID

        JOIN Book
        ON BookCopy.BookID = Book.BookID

        JOIN Member
        ON IssueTransaction.MemberID = Member.MemberID

        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "transaction_id":
            query += " AND IssueTransaction.TransactionID LIKE %s"

        elif search_by == "copy_id":
            query += " AND IssueTransaction.CopyID LIKE %s"

        elif search_by == "book_id":
            query += " AND BookCopy.BookID LIKE %s"

        elif search_by == "member_id":
            query += " AND Member.MemberID LIKE %s"

        elif search_by == "member_name":
            query += " AND Member.MemberName LIKE %s"

        else:
            query += " AND Book.BookName LIKE %s"

        values.append("%" + search + "%")

    if status_filter in ("Issued", "Returned"):
        query += " AND IssueTransaction.Status = %s"
        values.append(status_filter)

    if payment_filter in ("Paid", "Pending", "Waived"):
        query += " AND IssueTransaction.PaymentStatus=%s"
        values.append(payment_filter)
    if overdue_only:

        # Same rule get_overdue_days() uses: Issued + DueDate in the past.
        query += " AND IssueTransaction.Status='Issued' AND IssueTransaction.DueDate < %s"
        values.append(today.isoformat())

    sort_column = BORROW_SORT_COLUMNS[sort_by]
    sql_dir = "DESC" if sort_dir == "desc" else "ASC"

    query += f" ORDER BY {sort_column} {sql_dir}"

    cur.execute(query, values)

    raw_rows = cur.fetchall()

    transactions = []

    for row in raw_rows:

        (
            transaction_id, copy_id, book_id, book_name,
            member_id, member_name, issue_date, due_date,
            actual_return_date, status, stored_fine, payment_status,
            purchase_price
        ) = row

        if status == "Issued":

            overdue_days = get_overdue_days(due_date, today)
            fine_amount = calculate_fine(due_date, today, purchase_price)
            is_projected_fine = True

        else:

            overdue_days = get_overdue_days(due_date, actual_return_date)
            fine_amount = float(stored_fine or 0)
            is_projected_fine = False

        transactions.append({
            "transaction_id": transaction_id,
            "copy_id": copy_id,
            "book_id": book_id,
            "book_name": book_name,
            "member_id": member_id,
            "member_name": member_name,
            "issue_date": issue_date,
            "due_date": due_date,
            "actual_return_date": actual_return_date,
            "status": status,
            "overdue_days": overdue_days,
            "is_overdue": status == "Issued" and overdue_days > 0,
            "fine_amount": fine_amount,
            "is_projected_fine": is_projected_fine,
            "payment_status": payment_status,
        })

    return render_template(
        "borrow_books.html",
        total_issued=total_issued,
        total_overdue=total_overdue,
        returned_today=returned_today,
        outstanding_fine=outstanding_fine,
        active_members=active_members,
        available_copies=available_copies,
        borrow_limit=BORROW_LIMIT,
        loan_period_days=LOAN_PERIOD_DAYS,
        transactions=transactions,
        showing_count=len(transactions),
        search=search,
        search_by=search_by,
        status_filter=status_filter,
        payment_filter=payment_filter,
        overdue_only=overdue_only,
        sort_links=build_borrow_sort_links(sort_by, sort_dir),
        current_sort=sort_by,
        current_dir=sort_dir,
        today=today.isoformat()
    )

def build_borrow_sort_links(current_sort, current_dir):

    links = {}

    for column in BORROW_SORT_COLUMNS:

        args = request.args.to_dict()

        if current_sort == column and current_dir == "asc":
            args["dir"] = "desc"
        else:
            args["dir"] = "asc"

        args["sort"] = column

        links[column] = url_for("borrow_books", **args)

    return links

def get_active_members_with_issue_counts():
    cur.execute("""
        SELECT
            Member.MemberID,
            Member.MemberName,
            COUNT(IssueTransaction.TransactionID) AS issued_count
        FROM Member
        LEFT JOIN IssueTransaction
            ON Member.MemberID = IssueTransaction.MemberID
            AND IssueTransaction.Status='Issued'
        WHERE Member.IsActive=1
        GROUP BY Member.MemberID, Member.MemberName
        ORDER BY Member.MemberName
    """)
    return cur.fetchall()

def get_available_copies_for_issue():
    cur.execute("""
        SELECT
            BookCopy.CopyID,
            Book.BookName,
            BookCopy.BookID
        FROM BookCopy
        JOIN Book
            ON BookCopy.BookID = Book.BookID
        WHERE BookCopy.Status='Available'
        ORDER BY Book.BookName
    """)
    return cur.fetchall()

# ---------------- MEMBER MANAGEMENT ----------------

@app.route("/members")
def members():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    # Next Member ID, shown read-only in the Add form - same preview
    # pattern already used for next_category_id / next_book_id.

    next_member_id = generate_member_id()

    query = """
        SELECT
            Member.MemberID,
            Member.MemberName,
            Member.Phone,
            Member.Email,
            Member.Address,
            Member.JoinDate,
            Member.IsActive,
            COUNT(CASE WHEN IssueTransaction.Status='Issued' THEN 1 END),
            COALESCE(
                SUM(
                    CASE
                        WHEN IssueTransaction.PaymentStatus='Pending'
                        THEN IssueTransaction.FineAmount
                        ELSE 0
                    END
                ),
            0)
        FROM Member

        LEFT JOIN IssueTransaction
        ON Member.MemberID = IssueTransaction.MemberID

        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "phone":
            query += " AND Member.Phone LIKE %s"

        elif search_by == "email":
            query += " AND Member.Email LIKE %s"

        elif search_by == "member_id":
            query += " AND Member.MemberID LIKE %s"

        else:
            query += " AND Member.MemberName LIKE %s"

        values.append("%" + search + "%")

    query += """
        GROUP BY
        Member.MemberID,
        Member.MemberName,
        Member.Phone,
        Member.Email,
        Member.Address,
        Member.JoinDate,
        Member.IsActive

        ORDER BY Member.MemberID
    """

    cur.execute(query, values)

    all_members = cur.fetchall()

    return render_template(
        "members.html",
        members=all_members,
        total_members=len(all_members),
        next_member_id=next_member_id,
        today=date.today().isoformat(),
        search_by=search_by
    )

@app.route("/add_member", methods=["POST"])
def add_member():

    member_name = request.form["member_name"].strip().title()
    phone = request.form["phone"].strip()
    email = request.form["email"].strip().lower()
    address = request.form["address"].strip()
    join_date = request.form["join_date"]

    if (
        not member_name or
        not phone or
        not join_date
    ):

        flash("Please fill all required fields.")
        return redirect(url_for("members"))

    member_id = generate_member_id()

    try:

        cur.execute("""
            INSERT INTO Member
            (
                MemberID,
                MemberName,
                Phone,
                Email,
                Address,
                JoinDate,
                IsActive
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s
            )
        """, (
            member_id,
            member_name,
            phone,
            email,
            address,
            join_date,
            1
        ))

        conn.commit()

        flash("Member Added Successfully!")

    except mysql.connector.Error as e:

        conn.rollback()

        print(e)

        flash("Unable to add member.")

    return redirect(url_for("members"))

@app.route("/update_member", methods=["POST"])
def update_member():

    member_id = request.form["member_id"]
    member_name = request.form["member_name"].strip().title()
    phone = request.form["phone"].strip()
    email = request.form["email"].strip().lower()
    address = request.form["address"].strip()
    join_date = request.form["join_date"]

    if (
        not member_name or
        not phone or
        not join_date
    ):

        flash("Please fill all required fields.")
        return redirect(url_for("members"))

    cur.execute("""
        UPDATE Member
        SET
            MemberName=%s,
            Phone=%s,
            Email=%s,
            Address=%s,
            JoinDate=%s
        WHERE MemberID=%s
    """, (
        member_name,
        phone,
        email,
        address,
        join_date,
        member_id
    ))

    conn.commit()

    flash("Member Updated Successfully!")

    return redirect(url_for("members"))

@app.route("/deactivate_member/<member_id>")
def deactivate_member(member_id):

    # Members are never deleted - only deactivated. Deleting would
    # either cascade-destroy their IssueTransaction history or be
    # blocked by the FK, and the transaction/fine history must be
    # kept for reporting even after someone stops being a member.

    active_issues = get_active_issue_count(member_id)

    if active_issues > 0:

        flash("Cannot deactivate a member with books currently issued.")

        return redirect(url_for("members"))

    cur.execute("""
        UPDATE Member
        SET IsActive=0
        WHERE MemberID=%s
    """, (member_id,))

    conn.commit()

    flash("Member deactivated.")

    return redirect(url_for("members"))

@app.route("/reactivate_member/<member_id>")
def reactivate_member(member_id):

    cur.execute("""
        UPDATE Member
        SET IsActive=1
        WHERE MemberID=%s
    """, (member_id,))

    conn.commit()

    flash("Member reactivated.")

    return redirect(url_for("members"))

# ---------------- ISSUE BOOK ----------------

@app.route("/issue_book", methods=["POST"])
def issue_book():

    copy_id = request.form.get("copy_id", "").strip()
    member_id = request.form.get("member_id", "").strip()
    next_url = request.form.get("next") or url_for("inventory")

    if not copy_id or not member_id:

        flash("Please select both a Copy and a Member.")
        return redirect(next_url)

    # ---- Validate the copy ----

    cur.execute("""
        SELECT Status
        FROM BookCopy
        WHERE CopyID=%s
    """, (copy_id,))

    copy_row = cur.fetchone()

    if copy_row is None:

        flash("No such Book Copy exists.")
        return redirect(next_url)

    if copy_row[0] != "Available":

        flash(
            f"Copy {copy_id} is not Available (current status: {copy_row[0]}).")
        return redirect(next_url)

    # ---- Validate the member ----

    cur.execute("""
        SELECT IsActive
        FROM Member
        WHERE MemberID=%s
    """, (member_id,))

    member_row = cur.fetchone()

    if member_row is None:

        flash("No such Member exists.")
        return redirect(next_url)

    if member_row[0] != 1:

        flash("This Member is deactivated and cannot be issued books.")
        return redirect(next_url)

    # ---- Enforce the borrow limit ----

    active_issue_count = get_active_issue_count(member_id)

    if active_issue_count >= BORROW_LIMIT:

        flash(
            f"Member {member_id} already has {active_issue_count} books "
            f"issued (limit: {BORROW_LIMIT})."
        )
        return redirect(next_url)

    # ---- Create the IssueTransaction and flip the copy's Status ----

    transaction_id = generate_transaction_id()

    issue_date = date.today()
    due_date = issue_date + timedelta(days=LOAN_PERIOD_DAYS)

    try:

        cur.execute("""
            INSERT INTO IssueTransaction
            (
                TransactionID,
                CopyID,
                MemberID,
                IssueDate,
                DueDate,
                Status
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s
            )
        """, (
            transaction_id,
            copy_id,
            member_id,
            issue_date.isoformat(),
            due_date.isoformat(),
            "Issued"
        ))

        cur.execute("""
            UPDATE BookCopy
            SET Status='Issued'
            WHERE CopyID=%s
        """, (copy_id,))

        conn.commit()

        flash(
            f"Book Copy {copy_id} issued to Member {member_id}. "
            f"Due back on {due_date.isoformat()}."
        )

    except mysql.connector.Error as e:

        conn.rollback()

        print(e)

        flash("Unable to issue the book.")

    return redirect(next_url)

# ---------------- RETURN BOOK ----------------

@app.route("/return_book", methods=["POST"])
def return_book():
    copy_id = request.form.get("copy_id", "").strip()
    next_url = request.form.get("next") or url_for("inventory")

    if not copy_id:

        flash("Please select a Copy to return.")
        return redirect(next_url)

    # ---- Find the active transaction for this copy, together with the ----
    # ---- Book's PurchasePrice (needed for the fine cap), in one JOIN  ----

    cur.execute("""
        SELECT
            IssueTransaction.TransactionID,
            IssueTransaction.DueDate,
            Book.PurchasePrice
        FROM IssueTransaction

        JOIN BookCopy
        ON IssueTransaction.CopyID = BookCopy.CopyID

        JOIN Book
        ON BookCopy.BookID = Book.BookID

        WHERE
            IssueTransaction.CopyID = %s
            AND IssueTransaction.Status = 'Issued'
    """, (copy_id,))

    active_transaction = cur.fetchone()

    if active_transaction is None:

        flash(f"Copy {copy_id} does not have an active Issue to return.")
        return redirect(next_url)

    transaction_id, due_date, purchase_price = active_transaction

    actual_return_date = date.today()

    fine_amount = calculate_fine(due_date, actual_return_date, purchase_price)

    try:

        cur.execute("""
            UPDATE IssueTransaction
            SET
                ActualReturnDate=%s,
                Status='Returned',
                FineAmount=%s
            WHERE TransactionID=%s
        """, (
            actual_return_date.isoformat(),
            fine_amount,
            transaction_id
        ))

        cur.execute("""
            UPDATE BookCopy
            SET Status='Available'
            WHERE CopyID=%s
        """, (copy_id,))

        conn.commit()

        if fine_amount > 0:

            flash(
                f"Copy {copy_id} returned. Fine due: Rs {fine_amount:.2f} "
                f"(overdue since {due_date})."
            )

        else:

            flash(f"Copy {copy_id} returned on time. No fine due.")

    except mysql.connector.Error as e:

        conn.rollback()

        print(e)

        flash("Unable to return the book.")

    return redirect(next_url)

# ---------------- LIBRARY RULES ----------------

@app.route("/library_rules")
def library_rules():

    cur.execute("SELECT * FROM LibraryPolicy LIMIT 1")
    policy = cur.fetchone()

    if policy is None:
        flash("Library policy has not been configured yet.")
        return redirect(url_for("dashboard"))

    return render_template(
        "library_rules.html",
        policy=policy
    )

# ---------------- FINE PAYMENT ----------------

@app.route("/pay_fine", methods=["POST"])
def pay_fine():

    transaction_id = request.form.get("transaction_id", "").strip()
    payment_mode = request.form.get("payment_mode", "").strip()
    payment_date = request.form.get("payment_date", "").strip()
    next_url = request.form.get("next") or url_for("borrow_books")

    if not transaction_id or not payment_mode or not payment_date:

        flash("Please select a Payment Mode and Payment Date.")
        return redirect(next_url)

    if payment_mode not in VALID_PAYMENT_MODES:

        flash("Invalid Payment Mode.")
        return redirect(next_url)

    cur.execute("""
        SELECT 
        FineAmount,
        PaymentStatus, 
        Status
        FROM IssueTransaction
        WHERE TransactionID=%s
    """, (transaction_id,))

    txn_row = cur.fetchone()

    if txn_row is None:

        flash("No such Transaction exists.")
        return redirect(next_url)

    fine_amount, payment_status, status = txn_row

    if status != "Returned":

        flash("Fine can only be paid on a Returned transaction.")
        return redirect(next_url)

    if payment_status == "Paid":

        flash("This fine has already been paid.")
        return redirect(next_url)

    if not fine_amount or float(fine_amount) <= 0:

        flash("There is no outstanding fine on this transaction.")
        return redirect(next_url)

    payment_id = generate_payment_id()

    try:

        cur.execute("""
            INSERT INTO FinePayment
            (
                PaymentID,
                TransactionID,
                AmountPaid,
                PaymentMode,
                PaymentDate
            )
            VALUES
            (
                %s,%s,%s,%s,%s
            )
        """, (
            payment_id,
            transaction_id,
            fine_amount,
            payment_mode,
            payment_date
        ))

        cur.execute("""
            UPDATE IssueTransaction
            SET PaymentStatus='Paid'
            WHERE TransactionID=%s
        """, (transaction_id,))

        conn.commit()

        flash(
            f"Fine of Rs {float(fine_amount):.2f} marked as Paid via {payment_mode}.")

    except mysql.connector.Error as e:

        conn.rollback()

        print(e)

        flash("Unable to record the fine payment.")

    return redirect(next_url)
# ---------------- RUN FLASK ----------------


if __name__ == "__main__":
    app.run(debug=True)
