from flask import Blueprint, render_template, request, redirect, url_for, flash

from database import conn, cur

policy_bp = Blueprint("policy", __name__)


@policy_bp.route("/library_policy")
def library_policy():

    cur.execute("""
        SELECT *
        FROM LibraryPolicy
        WHERE PolicyID = 1
    """)

    policy = cur.fetchone()

    return render_template(
        "library_policy.html",
        policy=policy
    )


@policy_bp.route("/update_policy", methods=["POST"])
def update_policy():

    library_name = request.form["library_name"]

    # ---------------- Borrow Limit ----------------

    if request.form["book_limit_type"] == "limited":
        max_books = int(request.form["max_books"])
    else:
        max_books = -1

    # ---------------- Loan Period ----------------

    if request.form["loan_type"] == "limited":
        loan_days = int(request.form["loan_days"])
    else:
        loan_days = -1

    # ---------------- Membership ----------------

    if request.form["membership_type"] == "limited":
        membership_months = int(request.form["membership_months"])
    else:
        membership_months = -1

    # ---------------- Fine ----------------

    fine_rate = float(request.form["fine_rate"])
    increase_days = int(request.form["increase_days"])
    increase_rate = float(request.form["increase_rate"])
    fine_cap = float(request.form["fine_cap"])

    # ---------------- Renewal ----------------

    renewal = request.form["renewal_type"]

    if renewal == "none":

        allow_renewal = 0
        max_renewals = 0

    elif renewal == "limited":

        allow_renewal = 1
        max_renewals = int(request.form["max_renewals"])

    else:

        allow_renewal = 1
        max_renewals = -1

    # ---------------- Check if policy exists ----------------

    cur.execute("SELECT COUNT(*) FROM LibraryPolicy")
    exists = cur.fetchone()[0]

    if exists == 0:

        cur.execute("""
            INSERT INTO LibraryPolicy
            (
                LibraryName,
                MaxBooksPerMember,
                LoanPeriodDays,
                MembershipDurationMonths,
                FineBaseRate,
                FineIncreaseEveryDays,
                FineRateIncrease,
                FineCapBuffer,
                AllowRenewal,
                MaxRenewals
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            library_name,
            max_books,
            loan_days,
            membership_months,
            fine_rate,
            increase_days,
            increase_rate,
            fine_cap,
            allow_renewal,
            max_renewals
        ))

        flash("Library policy created successfully!")

    else:

        cur.execute("""
            UPDATE LibraryPolicy
            SET
                LibraryName=%s,
                MaxBooksPerMember=%s,
                LoanPeriodDays=%s,
                MembershipDurationMonths=%s,
                FineBaseRate=%s,
                FineIncreaseEveryDays=%s,
                FineRateIncrease=%s,
                FineCapBuffer=%s,
                AllowRenewal=%s,
                MaxRenewals=%s
        """,
        (
            library_name,
            max_books,
            loan_days,
            membership_months,
            fine_rate,
            increase_days,
            increase_rate,
            fine_cap,
            allow_renewal,
            max_renewals
        ))

        flash("Library policy updated successfully!")

    conn.commit()

    return redirect(url_for("policy.library_policy"))