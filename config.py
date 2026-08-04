
# BOOK COPY STATUS


COPY_AVAILABLE = "Available"
COPY_ISSUED = "Issued"
COPY_DAMAGED = "Damaged"
COPY_LOST = "Lost"

VALID_STATUSES = {
    COPY_AVAILABLE,
    COPY_ISSUED,
    COPY_DAMAGED,
    COPY_LOST,
}


# BOOK CONDITION


CONDITION_EXCELLENT = "Excellent"
CONDITION_GOOD = "Good"
CONDITION_FAIR = "Fair"
CONDITION_WORN = "Worn"
CONDITION_DAMAGED = "Damaged"
CONDITION_OTHER = "Other"

VALID_CONDITIONS = {
    CONDITION_EXCELLENT,
    CONDITION_GOOD,
    CONDITION_FAIR,
    CONDITION_WORN,
    CONDITION_DAMAGED,
    CONDITION_OTHER,
}


# SHELF STATUS


SHELF_ACTIVE = "Active"
SHELF_INACTIVE = "Inactive"

VALID_SHELF_STATUS = {
    SHELF_ACTIVE,
    SHELF_INACTIVE,
}


# MEMBER STATUS


MEMBER_ACTIVE = 1
MEMBER_INACTIVE = 0


# BORROW TRANSACTION STATUS


BORROW_ISSUED = "Issued"
BORROW_RETURNED = "Returned"

VALID_BORROW_STATUS = {
    BORROW_ISSUED,
    BORROW_RETURNED,
}


# PAYMENT STATUS


PAYMENT_PENDING = "Pending"
PAYMENT_PAID = "Paid"
PAYMENT_WAIVED = "Waived"

VALID_PAYMENT_STATUS = {
    PAYMENT_PENDING,
    PAYMENT_PAID,
    PAYMENT_WAIVED,
}


# PAYMENT MODES


PAYMENT_CASH = "Cash"
PAYMENT_UPI = "UPI"
PAYMENT_CARD = "Card"

VALID_PAYMENT_MODES = {
    PAYMENT_CASH,
    PAYMENT_UPI,
    PAYMENT_CARD,
}


# INVENTORY SORT COLUMNS


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


# BORROW SORT COLUMNS


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


# LIBRARY SETTINGS


BORROW_LIMIT = 5
LOAN_PERIOD_DAYS = 14

# FINE SETTINGS

FINE_BASE_RATE = 5
FINE_RATE_STEP = 5
FINE_MONTH_LENGTH_DAYS = 30
FINE_CAP_BUFFER = 100
