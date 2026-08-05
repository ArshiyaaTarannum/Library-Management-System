from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from datetime import date, timedelta

import mysql.connector

from database import conn, cur

from config import (
    BORROW_LIMIT,
    LOAN_PERIOD_DAYS,
    BORROW_SORT_COLUMNS,
    VALID_PAYMENT_MODES,
)
from helpers.borrow_helper import (
    generate_transaction_id,
    generate_payment_id,
    get_active_issue_count,
    get_overdue_days,
    calculate_fine,
    build_borrow_sort_links,
    get_active_members_with_issue_counts,
    get_available_copies_for_issue
)

borrow_bp = Blueprint("borrow", __name__)

@borrow_bp.route("/issue_book", methods=["POST"])
def issue_book():

    copy_id = request.form.get("copy_id", "").strip()
    member_id = request.form.get("member_id", "").strip()
    next_url = request.form.get("next") or url_for("inventory.inventory")

    if not copy_id or not member_id:
        flash("Please select both a Copy and a Member.")
        return redirect(next_url)

    # Validate the copy

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
            f"Copy {copy_id} is not Available "
            f"(current status: {copy_row[0]})."
        )
        return redirect(next_url)

    # Validate the member

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

    # Borrow limit

    active_issue_count = get_active_issue_count(member_id)

    if active_issue_count >= BORROW_LIMIT:
        flash(
            f"Member {member_id} already has "
            f"{active_issue_count} books issued "
            f"(limit: {BORROW_LIMIT})."
        )
        return redirect(next_url)

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
            (%s,%s,%s,%s,%s,%s)
        """, (
            transaction_id,
            copy_id,
            member_id,
            issue_date.isoformat(),
            due_date.isoformat(),
            "Issued"
        ))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Unable to issue the book.")
            return redirect(next_url)

        cur.execute("""
            UPDATE BookCopy
            SET Status='Issued'
            WHERE CopyID=%s
        """, (copy_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Book copy not found.")
            return redirect(next_url)

        conn.commit()

        flash(
            f"Book Copy {copy_id} issued to Member {member_id}. "
            f"Due back on {due_date.isoformat()}."
        )

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to issue the book.")

    return redirect(next_url)

@borrow_bp.route("/return_book", methods=["POST"])
def return_book():

    copy_id = request.form.get("copy_id", "").strip()
    next_url = request.form.get("next") or url_for("inventory.inventory")

    if not copy_id:
        flash("Please select a Copy to return.")
        return redirect(next_url)

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
            IssueTransaction.CopyID=%s
            AND IssueTransaction.Status='Issued'
    """, (copy_id,))

    active_transaction = cur.fetchone()

    if active_transaction is None:
        flash(f"Copy {copy_id} does not have an active Issue to return.")
        return redirect(next_url)

    transaction_id, due_date, purchase_price = active_transaction

    actual_return_date = date.today()
    fine_amount = calculate_fine(
        due_date,
        actual_return_date,
        purchase_price
    )

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

        if cur.rowcount == 0:
            conn.rollback()
            flash("Transaction not found.")
            return redirect(next_url)

        cur.execute("""
            UPDATE BookCopy
            SET Status='Available'
            WHERE CopyID=%s
        """, (copy_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Book copy not found.")
            return redirect(next_url)

        conn.commit()

        if fine_amount > 0:
            flash(
                f"Copy {copy_id} returned. "
                f"Fine due: Rs {fine_amount:.2f} "
                f"(overdue since {due_date})."
            )
        else:
            flash(f"Copy {copy_id} returned on time. No fine due.")

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to return the book.")

    return redirect(next_url)

@borrow_bp.route("/borrow_books")
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

    # ---------- Dashboard ----------

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Issued'
    """)
    total_issued = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Issued'
        AND DueDate < %s
    """, (today.isoformat(),))
    total_overdue = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM IssueTransaction
        WHERE Status='Returned'
        AND ActualReturnDate=%s
    """, (today.isoformat(),))
    returned_today = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(FineAmount), 0)
        FROM IssueTransaction
        WHERE Status='Returned'
        AND PaymentStatus='Pending'
    """)
    outstanding_fine = cur.fetchone()[0]

    active_members = get_active_members_with_issue_counts()
    available_copies = get_available_copies_for_issue()

    # ---------- Borrow Table ----------

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

        column = "Book.BookName"

        if search_by == "transaction_id":
            column = "IssueTransaction.TransactionID"

        elif search_by == "copy_id":
            column = "IssueTransaction.CopyID"

        elif search_by == "book_id":
            column = "BookCopy.BookID"

        elif search_by == "member_id":
            column = "Member.MemberID"

        elif search_by == "member_name":
            column = "Member.MemberName"

        query += f" AND {column} LIKE %s"
        values.append(f"%{search}%")

    if status_filter in ("Issued", "Returned"):
        query += " AND IssueTransaction.Status=%s"
        values.append(status_filter)

    if payment_filter in ("Paid", "Pending", "Waived"):
        query += " AND IssueTransaction.PaymentStatus=%s"
        values.append(payment_filter)

    if overdue_only:
        query += """
            AND IssueTransaction.Status='Issued'
            AND IssueTransaction.DueDate < %s
        """
        values.append(today.isoformat())

    sort_column = BORROW_SORT_COLUMNS[sort_by]
    sql_dir = "DESC" if sort_dir == "desc" else "ASC"

    query += f" ORDER BY {sort_column} {sql_dir}"

    cur.execute(query, values)
    raw_rows = cur.fetchall()

    transactions = []

    for row in raw_rows:

        (
            transaction_id,
            copy_id,
            book_id,
            book_name,
            member_id,
            member_name,
            issue_date,
            due_date,
            actual_return_date,
            status,
            stored_fine,
            payment_status,
            purchase_price
        ) = row

        if status == "Issued":
            overdue_days = get_overdue_days(due_date, today)
            fine_amount = calculate_fine(
                due_date,
                today,
                purchase_price
            )
            is_projected_fine = True

        else:
            overdue_days = get_overdue_days(
                due_date,
                actual_return_date
            )
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
            "is_overdue": (
                status == "Issued"
                and overdue_days > 0
            ),
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
        sort_links=build_borrow_sort_links(
            sort_by,
            sort_dir
        ),
        current_sort=sort_by,
        current_dir=sort_dir,
        today=today.isoformat()
    )

@borrow_bp.route("/pay_fine", methods=["POST"])
def pay_fine():

    transaction_id = request.form.get("transaction_id", "").strip()
    payment_mode = request.form.get("payment_mode", "").strip()
    payment_date = request.form.get("payment_date", "").strip()

    next_url = (
        request.form.get("next")
        or url_for("borrow.borrow_books")
    )

    if (
        not transaction_id
        or not payment_mode
        or not payment_date
    ):
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
        flash("Transaction not found.")
        return redirect(next_url)

    fine_amount, payment_status, status = txn_row

    if status != "Returned":
        flash("Fine can only be paid for returned books.")
        return redirect(next_url)

    if payment_status == "Paid":
        flash("This fine has already been paid.")
        return redirect(next_url)

    if not fine_amount or float(fine_amount) <= 0:
        flash("There is no outstanding fine for this transaction.")
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

        if cur.rowcount == 0:
            conn.rollback()
            flash("Transaction not found.")
            return redirect(next_url)

        conn.commit()

        flash(
            f"Fine of Rs {float(fine_amount):.2f} "
            f"paid successfully via {payment_mode}."
        )

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to record the fine payment.")

    return redirect(next_url)