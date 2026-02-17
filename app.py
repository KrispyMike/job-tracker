from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DB_NAME = "jobs.db"
LABOR_RATE = 55  # dollars per hour

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        job_name = request.form["job_name"]
        job_number = request.form["job_number"]
        client = request.form["client"]
        contract_amount = float(request.form["contract_amount"])
        est_labor_hours = float(request.form["est_labor_hours"])
        est_material_cost = float(request.form["est_material_cost"])

        cursor.execute("""
            INSERT INTO jobs 
            (job_name, job_number, client, contract_amount, est_labor_hours, est_material_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (job_name, job_number, client, contract_amount, est_labor_hours, est_material_cost))

        conn.commit()
        conn.close()
        return redirect("/")

    jobs = cursor.execute("SELECT * FROM jobs").fetchall()
    conn.close()

    return render_template("index.html", jobs=jobs)

@app.route("/job/<int:job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        crew_size = float(request.form["crew_size"])
        hours = float(request.form["hours"])
        material_cost = float(request.form["material_cost"])
        notes = request.form["notes"]

        cursor.execute("""
            INSERT INTO daily_reports
            (job_id, date, crew_size, hours, material_cost, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (job_id, date, crew_size, hours, material_cost, notes))

        conn.commit()
        return redirect(url_for("job_detail", job_id=job_id))

    job = cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    reports = cursor.execute("""
        SELECT * FROM daily_reports
        WHERE job_id = ?
    """, (job_id,)).fetchall()

    total_hours = sum(r["crew_size"] * r["hours"] for r in reports)
    total_labor_cost = total_hours * LABOR_RATE
    total_material_cost = sum(r["material_cost"] for r in reports)
    total_actual_cost = total_labor_cost + total_material_cost

    est_labor_cost = job["est_labor_hours"] * LABOR_RATE
    est_total_cost = est_labor_cost + job["est_material_cost"]
    est_margin = job["contract_amount"] - est_total_cost
    actual_margin = job["contract_amount"] - total_actual_cost

    # Overall percent used
    if est_total_cost > 0:
        percent_used = (total_actual_cost / est_total_cost) * 100
    else:
        percent_used = 0

    # Labor percent used
    if est_labor_cost > 0:
        labor_percent_used = (total_labor_cost / est_labor_cost) * 100
    else:
        labor_percent_used = 0

    # Material percent used
    if job["est_material_cost"] > 0:
        material_percent_used = (total_material_cost / job["est_material_cost"]) * 100
    else:
        material_percent_used = 0

    conn.close()

    return render_template(
        "job_detail.html",
        job=job,
        reports=reports,
        total_hours=total_hours,
        total_labor_cost=total_labor_cost,
        total_material_cost=total_material_cost,
        total_actual_cost=total_actual_cost,
        est_labor_cost=est_labor_cost,
        est_total_cost=est_total_cost,
        est_margin=est_margin,
        actual_margin=actual_margin,
        percent_used=percent_used,
        labor_percent_used=labor_percent_used,
        material_percent_used=material_percent_used,
        labor_rate=LABOR_RATE
    )

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            job_number TEXT,
            client TEXT,
            contract_amount REAL,
            est_labor_hours REAL,
            est_material_cost REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            date TEXT,
            crew_size REAL,
            hours REAL,
            material_cost REAL,
            notes TEXT
        )
    """)

    conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)