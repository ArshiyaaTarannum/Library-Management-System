from database import cur

def get_next_shelf_id():
    cur.execute("""
        SELECT ShelfID
        FROM Shelf
        ORDER BY ShelfID DESC
        LIMIT 1
    """)

    last = cur.fetchone()

    if last is None:
        return "SH001"

    number = int(last[0][2:]) + 1
    return f"SH{number:03d}"