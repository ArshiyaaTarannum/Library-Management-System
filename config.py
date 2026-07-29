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
