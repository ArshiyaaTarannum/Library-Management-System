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

    max_books = request.form["max_books"]

    loan_days = request.form["loan_days"]

    if request.form.get("lifetime_membership"):

        membership_months = -1

    else:

        membership_months = int(request.form["membership_months"])

    fine_rate = request.form["fine_rate"]

    increase_days = request.form["increase_days"]

    increase_rate = request.form["increase_rate"]

    fine_cap = request.form["fine_cap"]

    allow_renewal = 1 if request.form.get("allow_renewal") else 0

    if not allow_renewal:

        max_renewals = 0

    elif request.form.get("unlimited_renewals"):

        max_renewals = -1

    else:

        max_renewals = int(request.form["max_renewals"])
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

        WHERE PolicyID=1
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

    conn.commit()

    flash("Library policy updated successfully!")

    return redirect(url_for("policy.library_policy"))