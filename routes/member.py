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
from helpers.members_helper import generate_member_id
import mysql.connector
from database import conn, cur
members_bp=Blueprint("members", __name__)
from helpers.borrow_helper import get_active_issue_count

@members_bp.route("/members")
def members():

    search = request.args.get("search", "").strip()
    search_by = request.args.get("search_by", "")

    next_member_id = generate_member_id()

    query = """
        SELECT
            Member.MemberID,
            Member.MemberName,
            Member.Phone,
            Member.Email,
            Member.Address,
            Member.JoinDate,
            Member.IsActive,

            COUNT(
                CASE
                    WHEN IssueTransaction.Status='Issued'
                    THEN 1
                END
            ) AS ActiveIssues,

            COALESCE(
                SUM(
                    CASE
                        WHEN IssueTransaction.PaymentStatus='Pending'
                        THEN IssueTransaction.FineAmount
                        ELSE 0
                    END
                ),
                0
            ) AS PendingFine

        FROM Member

        LEFT JOIN IssueTransaction
        ON Member.MemberID = IssueTransaction.MemberID

        WHERE 1=1
    """

    values = []

    if search:

        column = "Member.MemberName"

        if search_by == "member_id":
            column = "Member.MemberID"

        elif search_by == "phone":
            column = "Member.Phone"

        elif search_by == "email":
            column = "Member.Email"

        query += f" AND {column} LIKE %s"

        values.append(f"%{search}%")

    query += """
        GROUP BY
            Member.MemberID,
            Member.MemberName,
            Member.Phone,
            Member.Email,
            Member.Address,
            Member.JoinDate,
            Member.IsActive

        ORDER BY Member.MemberID
    """

    cur.execute(query, values)
    all_members = cur.fetchall()

    return render_template(
        "members.html",
        members=all_members,
        total_members=len(all_members),
        next_member_id=next_member_id,
        today=date.today().isoformat(),
        search=search,
        search_by=search_by
    )

@members_bp.route("/add_member", methods=["POST"])
def add_member():

    member_name = request.form["member_name"].strip().title()
    phone = request.form["phone"].strip()
    email = request.form["email"].strip().lower()
    address = request.form["address"].strip()
    join_date = request.form["join_date"]

    if (
        not member_name
        or not phone
        or not join_date
    ):
        flash("Please fill all required fields.")
        return redirect(url_for("members.members"))

    member_id = generate_member_id()

    try:

        cur.execute("""
            INSERT INTO Member
            (
                MemberID,
                MemberName,
                Phone,
                Email,
                Address,
                JoinDate,
                IsActive
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s
            )
        """, (
            member_id,
            member_name,
            phone,
            email,
            address,
            join_date,
            1
        ))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Unable to add member.")
            return redirect(url_for("members.members"))

        conn.commit()
        flash("Member added successfully!")

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)

        if e.errno == 1062:
            flash("A member with the same phone number or email already exists.")
        else:
            flash("Unable to add member.")

    return redirect(url_for("members.members"))

@members_bp.route("/update_member", methods=["POST"])
def update_member():

    member_id = request.form["member_id"]
    member_name = request.form["member_name"].strip().title()
    phone = request.form["phone"].strip()
    email = request.form["email"].strip().lower()
    address = request.form["address"].strip()
    join_date = request.form["join_date"]

    if (
        not member_name
        or not phone
        or not join_date
    ):
        flash("Please fill all required fields.")
        return redirect(url_for("members.members"))

    try:

        cur.execute("""
            UPDATE Member
            SET
                MemberName=%s,
                Phone=%s,
                Email=%s,
                Address=%s,
                JoinDate=%s
            WHERE MemberID=%s
        """, (
            member_name,
            phone,
            email,
            address,
            join_date,
            member_id
        ))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Member not found.")
            return redirect(url_for("members.members"))

        conn.commit()
        flash("Member updated successfully!")

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)

        if e.errno == 1062:
            flash("A member with the same phone number or email already exists.")
        else:
            flash("Unable to update member.")

    return redirect(url_for("members.members"))

@members_bp.route("/deactivate_member/<member_id>", methods=["POST"])
def deactivate_member(member_id):

    active_issues = get_active_issue_count(member_id)

    if active_issues > 0:
        flash("Cannot deactivate a member with books currently issued.")
        return redirect(url_for("members.members"))

    try:

        cur.execute("""
            UPDATE Member
            SET IsActive = 0
            WHERE MemberID = %s
        """, (member_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Member not found.")
            return redirect(url_for("members.members"))

        conn.commit()
        flash("Member deactivated.")

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to deactivate member.")

    return redirect(url_for("members.members"))

@members_bp.route("/reactivate_member/<member_id>", methods=["POST"])
def reactivate_member(member_id):

    try:

        cur.execute("""
            UPDATE Member
            SET IsActive = 1
            WHERE MemberID = %s
        """, (member_id,))

        if cur.rowcount == 0:
            conn.rollback()
            flash("Member not found.")
            return redirect(url_for("members.members"))

        conn.commit()
        flash("Member reactivated.")

    except mysql.connector.Error as e:

        conn.rollback()
        current_app.logger.exception(e)
        flash("Unable to reactivate member.")

    return redirect(url_for("members.members"))