from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import date
import mysql.connector
from dotenv import load_dotenv
import json
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = "library_management_secret"

VALID_STATUSES = {"Available", "Issued", "Damaged", "Lost"}
VALID_CONDITIONS = {"Excellent", "Good", "Fair", "Worn", "Damaged", "Other"}
VALID_SHELF_STATUS = {"Active", "Inactive"}


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

# DATABASE CONNECTION 

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cur = conn.cursor()

# DASHBOARD PAGE 

@app.route("/")
def dashboard():
    return render_template("index.html")

# CATEGORY PAGE 

@app.route("/category")
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

    # Generate next Category ID

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


# ADD CATEGORY

@app.route("/add_category", methods=["POST"])
def add_category():

    category_name = request.form["category_name"].strip().title()

    if not category_name:
        flash("Please enter a category name.")
        return redirect(url_for("category"))

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

    return redirect(url_for("category"))


# DELETE CATEGORY 

@app.route("/delete_category/<category_id>")
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

    return redirect(url_for("category"))

# DELETE BOOK

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

@app.route("/update_category", methods=["POST"])
def update_category():

    category_id = request.form["category_id"]
    category_name = request.form["category_name"].strip().title()

    if not category_name:

        flash("Category name cannot be empty.")

        return redirect(url_for("category"))

    cur.execute("""
        UPDATE Category
        SET CategoryName=%s
        WHERE CategoryID=%s
    """, (category_name, category_id))

    conn.commit()

    flash("Category Updated Successfully!")

    return redirect(url_for("category"))   

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
        not book_name or
        not author or
        not category_id or
        not publication or
        not publication_date or
        not entry_date or
        not language or
        not edition or
        not purchase_price
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

    cur.execute("""
        SELECT ShelfID, ShelfName
        FROM Shelf
        WHERE Status='Active'
        ORDER BY ShelfName
    """)
    shelves = cur.fetchall()

    return render_template(
        "inventory.html",
        total_books=total_books,
        total_copies=total_copies,
        available=available,
        issued=issued,
        damaged=damaged,
        lost=lost,
        copies=copies,
        shelves=shelves,
        showing_count=len(copies),
        search=search,
        search_by=search_by,
        status_filter=status_filter,
        condition_filter=condition_filter,
        valid_statuses=sorted(VALID_STATUSES),
        valid_conditions=sorted(VALID_CONDITIONS),
        sort_links=build_inventory_sort_links(sort_by, sort_dir),
        current_sort=sort_by,
        current_dir=sort_dir
    )


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


# ---------------- RUN FLASK ----------------


if __name__ == "__main__":
    app.run(debug=True)
