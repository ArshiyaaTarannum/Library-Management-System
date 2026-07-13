from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import date
import mysql.connector

app = Flask(__name__)
app.secret_key = "library_management_secret"

# ---------------- DATABASE CONNECTION ----------------

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@rasulpur489",
    database="library"
)

cur = conn.cursor()

# ---------------- DASHBOARD PAGE ----------------


@app.route("/")
def dashboard():
    return render_template("index.html")

# ---------------- CATEGORY PAGE ----------------

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


# ---------------- ADD CATEGORY ----------------

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


# ---------------- DELETE CATEGORY ----------------

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

# ---------------- DELETE BOOK ----------------


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

    if (
        not book_name or
        not author or
        not category_id or
        not publication or
        not publication_date or
        not entry_date
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
            PublicationDate=%s
            EntryDate=%s
        WHERE BookID=%s
    """, (
        book_name,
        author,
        category_id,
        publication,
        publication_date,
        entry_date,
        book_id
    ))

    conn.commit()

    flash("Book Updated Successfully!")

    return redirect(url_for("add_books"))

@app.route("/add_books")
def add_books():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    cur.execute("""
        SELECT CategoryID, CategoryName
        FROM Category
        ORDER BY CategoryName
    """)
    categories = cur.fetchall()

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
            Book.EntryDate
        FROM Book
        JOIN Category
        ON Book.CategoryID = Category.CategoryID
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

    query += " ORDER BY Book.BookID"

    cur.execute(query, values)

    books = cur.fetchall()
    total_books = len(books)

    return render_template(
        "add_books.html",
        categories=categories,
        next_book_id=next_book_id,
        books=books,
        today=date.today().isoformat(),
        total_books=total_books
    )

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
            Book.EntryDate
        FROM Book
        JOIN Category
        ON Book.CategoryID = Category.CategoryID
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

    query += " ORDER BY Book.BookID"

    cur.execute(query, values)

    books = cur.fetchall()

    return render_template(
        "view_books.html",
        books=books
    )

@app.route("/add_book", methods=["POST"])
def add_book():

    book_name = request.form["book_name"].strip().title()
    author = request.form["author"].strip().title()
    category_id = request.form["category_id"]
    publication = request.form["publication"].strip().title()
    publication_date = request.form["publication_date"]
    entry_date = request.form["entry_date"]

    if (
        not book_name or
        not author or
        not category_id or
        not publication or
        not publication_date or
        not entry_date
    ):
        flash("Please fill all fields.")
        return redirect(url_for("add_books"))

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

    try:

        cur.execute("""
            INSERT INTO Book
            (
                BookID,
                BookName,
                Author,
                CategoryID,
                Publication,
                PublicationDate,
                EntryDate
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            book_id,
            book_name,
            author,
            category_id,
            publication,
            publication_date,
            entry_date
        ))

        conn.commit()

        flash("Book Added Successfully!")

    except mysql.connector.Error as e:

        print(e)
        flash("Unable to add book.")

    return redirect(url_for("add_books"))

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


@app.route("/borrow_books")
def borrow_books():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    # ---------------- Available Books ----------------

    cur.execute("""
        SELECT BookID, BookName
        FROM Book
        WHERE Status='Available'
        ORDER BY BookName
    """)

    books = cur.fetchall()

    # ---------------- Generate Next Issue ID ----------------

    cur.execute("""
        SELECT IssueID
        FROM BorrowBook
        ORDER BY IssueID DESC
        LIMIT 1
    """)

    last_issue = cur.fetchone()

    if last_issue is None:
        next_issue_id = "ISS001"
    else:
        number = int(last_issue[0][3:]) + 1
        next_issue_id = f"ISS{number:03d}"

    # ---------------- Borrow Records ----------------

    query = """
        SELECT
            BorrowBook.IssueID,
            BorrowBook.BookID,
            Book.BookName,
            BorrowBook.StudentName,
            BorrowBook.StudentID,
            BorrowBook.IssueDate,
            BorrowBook.DueDate,
            BorrowBook.ReturnDate,
            BorrowBook.EntryDate,
            BorrowBook.Status
        FROM BorrowBook
        JOIN Book
        ON BorrowBook.BookID = Book.BookID
        WHERE 1=1
    """

    values = []

    if search:

        if search_by == "issue_id":
            query += " AND BorrowBook.IssueID LIKE %s"

        elif search_by == "student_name":
            query += " AND BorrowBook.StudentName LIKE %s"

        elif search_by == "student_id":
            query += " AND BorrowBook.StudentID LIKE %s"

        elif search_by == "book":
            query += " AND Book.BookName LIKE %s"

        else:
            query += " AND BorrowBook.Status LIKE %s"

        values.append("%" + search + "%")

    query += " ORDER BY BorrowBook.IssueDate DESC"

    cur.execute(query, values)

    borrow_records = cur.fetchall()

    today = date.today().isoformat()

    return render_template(
        "borrow_books.html",
        books=books,
        borrow_records=borrow_records,
        next_issue_id=next_issue_id,
        today=today
    )

# ---------------- RUN FLASK ----------------


if __name__ == "__main__":
    app.run(debug=True)
