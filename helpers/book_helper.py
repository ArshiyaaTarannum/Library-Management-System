from database import cur

def get_next_book_id():
    cur.execute("""
        SELECT BookID
        FROM Book
        ORDER BY BookID DESC
        LIMIT 1
    """)

    last_book = cur.fetchone()

    if last_book is None:
        return "LIB0001"

    number = int(last_book[0][3:]) + 1
    return f"LIB{number:04d}"