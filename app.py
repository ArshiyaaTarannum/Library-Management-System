from flask import Flask, flash, redirect, render_template, request, url_for

from database import cur
from routes.category import category_bp
from routes.policy import policy_bp
from routes.books import books_bp
from routes.copy import copies_bp
from routes.shelf import shelf_bp
from routes.inventory import inventory_bp
from routes.member import members_bp
from routes.borrow import borrow_bp

app = Flask(__name__)
app.secret_key = "library_management_secret"
app.register_blueprint(category_bp)
app.register_blueprint(policy_bp)
app.register_blueprint(books_bp)
app.register_blueprint(copies_bp)
app.register_blueprint(shelf_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(members_bp)
app.register_blueprint(borrow_bp)

# INDEX PAGE

@app.route("/")
def index():
    return render_template("index.html")

# ---------------- LIBRARY RULES ----------------

@app.route("/library_rules")
def library_rules():

    cur.execute("SELECT * FROM LibraryPolicy LIMIT 1")
    policy = cur.fetchone()

    if policy is None:
        flash("Library policy has not been configured yet.")
        return redirect(url_for("index"))

    return render_template(
        "library_rules.html",
        policy=policy
    )


@app.route("/dashboard")
def dashboard():

    # ---------- Statistics ----------

    cur.execute("SELECT COUNT(*) FROM Book")
    total_books = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM BookCopy")
    total_copies = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM Member
        WHERE IsActive = 1
    """)
    total_members = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status = 'Issued'
    """)
    issued_books = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status = 'Issued'
        AND DueDate < CURDATE()
    """)
    overdue_books = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM Shelf
        WHERE Status = 'Active'
    """)
    total_shelves = cur.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_books=total_books,
        total_copies=total_copies,
        total_members=total_members,
        issued_books=issued_books,
        overdue_books=overdue_books,
        total_shelves=total_shelves
    )
# ---------------- RUN FLASK ----------------


if __name__ == "__main__":
    app.run(debug=True)
