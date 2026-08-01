from datetime import date

from flask import request, url_for

from database import cur

from config import (
    BORROW_SORT_COLUMNS,
    FINE_BASE_RATE,
    FINE_RATE_STEP,
    FINE_MONTH_LENGTH_DAYS,
    FINE_CAP_BUFFER
)

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
        WHERE MemberID=%s
        AND Status='Issued'
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

        days_in_this_block = min(
            FINE_MONTH_LENGTH_DAYS,
            remaining_days
        )

        rate_for_this_block = (
            FINE_BASE_RATE
            + (FINE_RATE_STEP * (month_number - 1))
        )

        fine += days_in_this_block * rate_for_this_block

        remaining_days -= days_in_this_block
        month_number += 1

    cap = float(purchase_price or 0) + FINE_CAP_BUFFER

    return round(min(fine, cap), 2)

def build_borrow_sort_links(current_sort, current_dir):

    links = {}

    for column in BORROW_SORT_COLUMNS:

        args = request.args.to_dict()

        if current_sort == column and current_dir == "asc":
            args["dir"] = "desc"
        else:
            args["dir"] = "asc"

        args["sort"] = column

        links[column] = url_for("borrow.borrow_books", **args)

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

        GROUP BY
            Member.MemberID,
            Member.MemberName

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