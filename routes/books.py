from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from datetime import date
import json
import mysql.connector

from config import (
    VALID_STATUSES,
    VALID_CONDITIONS,
    COPY_AVAILABLE
)
from database import conn, cur
from helpers.book_helper import get_next_book_id
books_bp = Blueprint("books", __name__)
@books_bp.route("/delete_book/<book_id>", methods=["POST"])
def delete_book(book_id):

    try:
        cur.execute("""
            DELETE FROM Book
            WHERE BookID=%s
        """, (book_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Book not found.")
            return redirect(url_for("books.add_books"))

        conn.commit()
        flash("Book deleted successfully!")

    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)

        if e.errno == 1451:
            flash("This book still has copies on record. Remove or reassign its copies before deleting the book.")
        else:
            flash("Unable to delete the book.")

    return redirect(url_for("books.add_books"))

@books_bp.route("/update_book", methods=["POST"])
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
    try:
        purchase_price = float(request.form["purchase_price"])
        if purchase_price < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Purchase Price must be a valid non-negative number.")
        return redirect(url_for("books.add_books"))

    if (
        not book_id
        or not book_name
        or not author
        or not category_id
        or not publication
        or not publication_date
        or not entry_date
        or not language
        or not edition
    ):
        flash("Please fill all fields.")
        return redirect(url_for("books.add_books"))


    try:
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

        if cur.rowcount == 0:
            conn.rollback()
            flash("Book not found.")
            return redirect(url_for("books.add_books"))

        conn.commit()
        flash("Book Updated Successfully!")

    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to update the book.")

    return redirect(url_for("books.add_books"))

@books_bp.route("/add_books")
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
    # FIX: now uses the shared helper instead of duplicating this logic.
    next_book_id = get_next_book_id()

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
            COUNT(BookCopy.CopyID) AS TotalCopies,
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
    books_list = cur.fetchall()

    return render_template(
        "add_books.html",
        categories=categories,
        shelves=shelves,
        next_book_id=next_book_id,
        books=books_list,
        today=date.today().isoformat(),
        total_books=len(books_list)
    )

@books_bp.route("/add_book", methods=["POST"])
def add_book():

    book_name = request.form["book_name"].strip().title()
    author = request.form["author"].strip().title()
    category_id = request.form["category_id"]
    publication = request.form["publication"].strip().title()
    publication_date = request.form["publication_date"]

    entry_date = request.form.get("entry_date", "").strip()
    if not entry_date:
        entry_date = date.today().isoformat()

    language = request.form["language"].strip().title()
    edition = request.form["edition"].strip()

    try:
        total_copies = int(request.form["total_copies"])
    except (ValueError, TypeError):
        flash("Invalid Total Copies.")
        return redirect(url_for("books.add_books"))

    try:
        purchase_price = float(request.form["purchase_price"])
        if purchase_price < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Purchase Price must be a valid non-negative number.")
        return redirect(url_for("books.add_books"))

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
        return redirect(url_for("books.add_books"))

    try:
        copy_groups = json.loads(copy_groups_raw)
    except (json.JSONDecodeError, TypeError):
        flash("Copy allocation data was missing or invalid. Please try again.")
        return redirect(url_for("books.add_books"))

    if not isinstance(copy_groups, list) or not copy_groups:
        flash("Please provide at least one copy allocation group.")
        return redirect(url_for("books.add_books"))

    cleaned_groups = []
    allocated = 0

    for group in copy_groups:

        if not isinstance(group, dict):
            flash("Copy allocation data was malformed. Please try again.")
            return redirect(url_for("books.add_books"))

        try:
            quantity = int(group.get("quantity", 0))
        except (TypeError, ValueError):
            flash("Every group needs a valid whole number of copies.")
            return redirect(url_for("books.add_books"))

        shelf = str(group.get("shelf", "")).strip()
        status = COPY_AVAILABLE
        condition = str(group.get("condition", "")).strip()
        remark = str(group.get("remark", "")).strip()

        if quantity < 1:
            flash("Every group must contain at least 1 copy.")
            return redirect(url_for("books.add_books"))

        if not shelf:
            flash("Every group needs a Shelf.")
            return redirect(url_for("books.add_books"))

        if status not in VALID_STATUSES:
            flash("Every group needs a valid Status.")
            return redirect(url_for("books.add_books"))

        if condition not in VALID_CONDITIONS:
            flash("Every group needs a valid Condition.")
            return redirect(url_for("books.add_books"))

        cur.execute("""
            SELECT Capacity
            FROM Shelf
            WHERE ShelfID=%s
        """, (shelf,))
        row = cur.fetchone()

        if row is None:
            flash("Selected shelf does not exist.")
            return redirect(url_for("books.add_books"))

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
                f"{capacity - current_books} spaces remaining."
            )
            return redirect(url_for("books.add_books"))

        cleaned_groups.append(
            (quantity, shelf, COPY_AVAILABLE, condition, remark))
        allocated += quantity

    if allocated != total_copies:
        flash(
            f"Allocated copies ({allocated}) do not match "
            f"Total Copies ({total_copies})."
        )
        return redirect(url_for("books.add_books"))

    try:
        # Generate Book ID
        # FIX: now uses the shared helper instead of duplicating this logic.
        book_id = get_next_book_id()

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
        """, (
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
        flash(f"Book Added Successfully with {total_copies} copies!")

    except mysql.connector.Error as e:
        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to add book.")

    return redirect(url_for("books.add_books"))

@books_bp.route("/books")
def view_books():

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
            COUNT(BookCopy.CopyID) AS TotalCopies,
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

        column = "Book.BookName"

        if search_by == "book_id":
            column = "Book.BookID"

        elif search_by == "author":
            column = "Book.Author"

        elif search_by == "publication":
            column = "Book.Publication"

        elif search_by == "category":
            column = "Category.CategoryName"

        query += f" AND {column} LIKE %s"

        values.append(f"%{search}%")

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
        books=books,
        total_books=len(books)
    )