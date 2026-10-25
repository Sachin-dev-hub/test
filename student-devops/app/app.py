import os
import re
import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384

def connect():
    return psycopg.connect(host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "students"), user=os.getenv("DB_USER", "studentapp"),
        password=os.environ["DB_PASSWORD"], connect_timeout=3, row_factory=dict_row)

def validate(data):
    if not isinstance(data, dict):
        return None
    fields = {k: data.get(k) for k in ("name", "email", "course")}
    if any(not isinstance(v, str) for v in fields.values()):
        return None
    fields = {k: v.strip() for k, v in fields.items()}
    fields["email"] = fields["email"].lower()
    if not (1 <= len(fields["name"]) <= 100 and 1 <= len(fields["course"]) <= 100
            and len(fields["email"]) <= 254
            and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", fields["email"])):
        return None
    return fields

@app.errorhandler(psycopg.Error)
def database_error(error):
    if isinstance(error, psycopg.errors.UniqueViolation):
        return jsonify(error="Email already registered"), 409
    app.logger.error("Database operation failed (%s)", type(error).__name__)
    return jsonify(error="Database temporarily unavailable"), 503

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/health/live")
def live():
    return jsonify(status="alive", version=os.getenv("APP_VERSION", "v2"))

@app.get("/health/ready")
def ready():
    with connect() as db:
        db.execute("SELECT id FROM students LIMIT 1")
    return jsonify(status="ready")

@app.get("/api/students")
def list_students():
    with connect() as db:
        rows = db.execute("SELECT id, name, email, course FROM students ORDER BY id DESC LIMIT 500").fetchall()
    return jsonify(rows)

@app.route("/api/students", methods=["POST"])
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def save_student(student_id=None):
    data = validate(request.get_json(silent=True))
    if data is None:
        return jsonify(error="Provide name, valid email, and course; name/course max 100 characters"), 400
    with connect() as db:
        if student_id is None:
            row = db.execute("INSERT INTO students(name,email,course) VALUES (%s,%s,%s) RETURNING id,name,email,course",
                (data["name"], data["email"], data["course"])).fetchone()
        else:
            row = db.execute("UPDATE students SET name=%s,email=%s,course=%s WHERE id=%s RETURNING id,name,email,course",
                (data["name"], data["email"], data["course"], student_id)).fetchone()
    if row is None:
        return jsonify(error="Student not found"), 404
    return jsonify(row), 201 if student_id is None else 200

@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    with connect() as db:
        row = db.execute("DELETE FROM students WHERE id=%s RETURNING id", (student_id,)).fetchone()
    if row is None:
        return jsonify(error="Student not found"), 404
    return "", 204
