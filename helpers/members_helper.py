from database import cur

def generate_member_id():



    cur.execute("""

        SELECT MemberID

        FROM Member

        ORDER BY MemberID DESC

        LIMIT 1

    """)



    last_member = cur.fetchone()



    if last_member is None:

        return "MEM0001"



    number = int(last_member[0][3:]) + 1

    return f"MEM{number:04d}"
