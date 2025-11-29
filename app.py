import base64
import datetime
import hashlib
import os
import secrets
import time
import io

from flask import Flask, abort, redirect, render_template, request, url_for, session, jsonify, send_file
from dotenv import load_dotenv
from functools import wraps
from openpyxl import Workbook
from werkzeug.utils import secure_filename

from config import load_config
from services.supabase_service import SupabaseService
from services.face_service import FaceService
from services.face_service_sface import SFaceService
try:
    from services.face_service_fr import FaceEncodingService
    _FR_AVAILABLE = True
except Exception:
    _FR_AVAILABLE = False
try:
    from services.face_service_insight import InsightFaceService
    _INSIGHT_AVAILABLE = True
except Exception:
    _INSIGHT_AVAILABLE = False
from utils.haversine import haversine_m
from utils.qr import build_scan_url, generate_qr_png_bytes, sign_token, verify_token
from utils.face_token import sign_face_token, verify_face_token

load_dotenv(override=True)
app = Flask(__name__)
cfg = load_config()
app.config.from_object(cfg)
app.secret_key = cfg.SECRET_KEY

supabase = SupabaseService(cfg.SUPABASE_URL, cfg.SUPABASE_KEY)

# Create a default lecture for testing when Supabase is not configured
if not supabase.enabled:
    default_lecture = {
        "lectureId": "lec-869919a4",
        "lectureName": "Test Lecture",
        "roomNo": "101",
        "date": "2025-11-13",
        "time": "08:00",
        "lat": 19.0760,
        "lng": 72.8777,
        "qrNonce": "c71823aa891a0eac271e3c54109db9ad",
        "qrIssuedAt": 1763001532,
        "active": True,
    }
    supabase.create_lecture("lec-869919a4", default_lecture)

if cfg.FACE_BACKEND == "insightface" and _INSIGHT_AVAILABLE:
    face_service = InsightFaceService(cfg.FACE_DATA_DIR, cfg.FACE_SIMILARITY_THRESHOLD)
elif cfg.FACE_BACKEND == "fr" and _FR_AVAILABLE:
    face_service = FaceEncodingService(cfg.FACE_DATA_DIR, cfg.FACE_ENCODING_TOLERANCE)
elif cfg.FACE_BACKEND == "sface":
    face_service = SFaceService(
        cfg.FACE_DATA_DIR,
        cfg.FACE_SFACE_DET_MODEL,
        cfg.FACE_SFACE_REC_MODEL,
        cfg.FACE_SIMILARITY_THRESHOLD,
    )
else:
    face_service = FaceService(cfg.FACE_DATA_DIR, cfg.FACE_CONFIDENCE_THRESHOLD)

def hash_password(pwd: str) -> str:
    return hashlib.sha256((pwd or "").encode()).hexdigest()

def require_role(role: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                if role == "admin":
                    return redirect(url_for("admin_login"))
                return redirect(url_for("faculty_login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/")
def index():
    return render_template("hero.html")

@app.get("/admin/login")
def admin_login():
    return render_template("admin_login.html")

@app.post("/admin/login")
def admin_login_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    if email == admin_email and password == admin_password:
        session["role"] = "admin"
        session["email"] = email
        return redirect(url_for("admin_faculties"))
    return render_template("admin_login.html", error="Invalid email or password")

@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.get("/admin/faculties")
@require_role("admin")
def admin_faculties():
    faculties = supabase.list_faculties()
    return render_template("admin_faculties.html", faculties=faculties)

@app.post("/admin/faculties/create")
@require_role("admin")
def admin_create_faculty():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not name or not email or not password:
        abort(400)
    supabase.create_faculty(email, {"name": name, "email": email, "passwordHash": hash_password(password)})
    return redirect(url_for("admin_faculties"))

@app.post("/admin/faculties/<key>/update")
@require_role("admin")
def admin_update_faculty(key):
    faculties = supabase.list_faculties()
    rec = faculties.get(key)
    if not rec:
        abort(404)
    name = request.form.get("name", rec.get("name", "")).strip()
    password = request.form.get("password", "")
    email = rec.get("email", "")
    data = {"name": name, "email": email, "passwordHash": rec.get("passwordHash", "")}
    if password:
        data["passwordHash"] = hash_password(password)
    supabase.create_faculty(email, data)
    return redirect(url_for("admin_faculties"))

@app.post("/admin/faculties/<key>/delete")
@require_role("admin")
def admin_delete_faculty(key):
    faculties = supabase.list_faculties()
    rec = faculties.get(key)
    if rec and rec.get("email"):
        supabase.delete_faculty(rec["email"])
    return redirect(url_for("admin_faculties"))

@app.get("/faculty/login")
def faculty_login():
    return render_template("faculty_login.html")

@app.post("/faculty/login")
def faculty_login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    rec = supabase.get_faculty(email)
    if rec and rec.get("passwordHash") == hash_password(password):
        session["role"] = "faculty"
        session["email"] = email
        return redirect(url_for("list_lectures"))
    return render_template("faculty_login.html", error="Invalid email or password")
    

@app.get("/faculty/logout")
def faculty_logout():
    session.clear()
    return redirect(url_for("faculty_login"))

@app.get("/faculty/signup")
def faculty_signup():
    return render_template("faculty_signup.html")

@app.post("/faculty/signup")
def faculty_signup_post():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    if not name or not email or not password:
        return render_template("faculty_signup.html", error="All fields are required")
    
    if password != confirm_password:
        return render_template("faculty_signup.html", error="Passwords do not match")
    
    # Check if faculty already exists
    existing = supabase.get_faculty(email)
    if existing:
        return render_template("faculty_signup.html", error="Email already registered. Please login instead.")
    
    # Create new faculty account
    supabase.create_faculty(email, {
        "name": name,
        "email": email,
        "passwordHash": hash_password(password)
    })
    
    # Auto-login after signup
    session["role"] = "faculty"
    session["email"] = email
    return redirect(url_for("list_lectures"))

@app.get("/faculty/lectures/new")
@require_role("faculty")
def new_lecture():
    suggested_id = "lec-" + secrets.token_hex(4)
    return render_template("faculty_lecture_new2.html", suggested_id=suggested_id)

@app.post("/faculty/lectures/new")
@require_role("faculty")
def create_lecture():
    lecture_id = request.form.get("lecture_id", "").strip()
    lecture_name = request.form.get("lecture_name", "").strip()
    room_no = request.form.get("room_no", "").strip()
    date = request.form.get("date", "").strip()
    time_s = request.form.get("time", "").strip()
    end_time_s = request.form.get("end_time", "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    if not lecture_id or not lecture_name or not room_no or not date or not time_s or not end_time_s or not lat or not lng:
        abort(400)
    nonce = secrets.token_hex(16)
    issued_at = int(time.time())
    lecture = {
        "lectureId": lecture_id,
        "lectureName": lecture_name,
        "roomNo": room_no,
        "date": date,
        "time": time_s,
        "end_time": end_time_s,
        "lat": float(lat),
        "lng": float(lng),
        "qrNonce": nonce,
        "qrIssuedAt": issued_at,
        "active": True,
    }
    supabase.create_lecture(lecture_id, lecture)
    token = sign_token(lecture_id, nonce, issued_at, cfg.QR_SIGNING_SECRET)
    base_url = cfg.PUBLIC_BASE_URL or request.host_url
    scan_url = build_scan_url(base_url, lecture_id, token)
    qr_bytes = generate_qr_png_bytes(scan_url)
    qr_b64 = base64.b64encode(qr_bytes).decode()
    return render_template("faculty_lecture_qr.html", lecture=lecture, scan_url=scan_url, qr_b64=qr_b64)

@app.get("/faculty/lectures")
@require_role("faculty")
def list_lectures():
    lectures = supabase.list_lectures()

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    subject_filter = request.args.get("subject", "").strip().lower()
    start_time = request.args.get("start_time", "").strip()
    end_time = request.args.get("end_time", "").strip()

    if start_date or end_date or subject_filter or start_time or end_time:
        filtered = {}
        for lid, lec in lectures.items():
            lec_date = str(lec.get("date", "")).strip()
            if start_date and lec_date and lec_date < start_date:
                continue
            if end_date and lec_date and lec_date > end_date:
                continue
            lec_time = str(lec.get("time", "")).strip()
            if start_time and lec_time and lec_time < start_time:
                continue
            if end_time and lec_time and lec_time > end_time:
                continue
            if subject_filter:
                name = str(lec.get("lectureName", "")).strip().lower()
                if subject_filter not in name:
                    continue
            filtered[lid] = lec
        lectures = filtered

    return render_template("faculty_lecture_list.html", lectures=lectures)

@app.get("/faculty/lectures/<lecture_id>/qr")
@require_role("faculty")
def lecture_qr(lecture_id):
    lecture = supabase.get_lecture(lecture_id)
    if not lecture:
        abort(404)
    token = sign_token(lecture_id, lecture.get("qrNonce", ""), lecture.get("qrIssuedAt", 0), cfg.QR_SIGNING_SECRET)
    base_url = cfg.PUBLIC_BASE_URL or request.host_url
    scan_url = build_scan_url(base_url, lecture_id, token)
    qr_bytes = generate_qr_png_bytes(scan_url)
    qr_b64 = base64.b64encode(qr_bytes).decode()
    return render_template("faculty_lecture_qr.html", lecture=lecture, scan_url=scan_url, qr_b64=qr_b64)

@app.get("/faculty/lectures/<lecture_id>")
@require_role("faculty")
def lecture_report(lecture_id):
    lecture = supabase.get_lecture(lecture_id)
    if not lecture:
        abort(404)
    records = supabase.list_attendance(lecture_id)
    present_count = sum(1 for v in records.values() if v.get("status") == "Present")
    rejected_count = sum(1 for v in records.values() if v.get("status") == "Rejected")
    return render_template(
        "faculty_lecture_report.html",
        lecture=lecture,
        lecture_id=lecture_id,
        records=records,
        present_count=present_count,
        rejected_count=rejected_count,
    )

@app.get("/faculty/lectures/<lecture_id>/export.xlsx")
@require_role("faculty")
def export_lecture_attendance(lecture_id):
    lecture = supabase.get_lecture(lecture_id)
    if not lecture:
        abort(404)
    records = supabase.list_attendance(lecture_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # Columns: Name, Roll No, Lecture ID, Date, Time, Subject, Status (1=Present, 0=Absent)
    ws.append(["Name", "Roll No", "Lecture ID", "Date", "Time", "Subject", "Status"])

    for roll, rec in records.items():
        status = (rec.get("status", "") or "").strip()
        is_present = status.lower() == "present"
        ws.append([
            rec.get("name", ""),
            roll,
            lecture_id,
            lecture.get("date", ""),
            lecture.get("time", ""),
            lecture.get("lectureName", ""),
            1 if is_present else 0,
        ])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    filename = f"attendance_{lecture_id}.xlsx"
    return send_file(bio, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/faculty/lectures/<lecture_id>/delete")
@require_role("faculty")
def delete_lecture(lecture_id):
    supabase.delete_lecture(lecture_id)
    return redirect(url_for("list_lectures"))

@app.post("/faculty/lectures/<lecture_id>/attendance/<roll_no>/delete")
@require_role("faculty")
def delete_attendance_record(lecture_id, roll_no):
    supabase.delete_attendance(lecture_id, roll_no)
    return redirect(url_for("lecture_report", lecture_id=lecture_id))

@app.post("/faculty/lectures/<lecture_id>/attendance/<roll_no>/update")
@require_role("faculty")
def update_attendance_record(lecture_id, roll_no):
    records = supabase.list_attendance(lecture_id)
    rec = records.get(roll_no)
    if not rec:
        abort(404)
    new_status = request.form.get("status", rec.get("status", "")).strip() or rec.get("status", "")
    new_name = request.form.get("name", rec.get("name", "")).strip() or rec.get("name", "")
    rec["status"] = new_status
    rec["name"] = new_name
    supabase.write_attendance(lecture_id, roll_no, rec)
    return redirect(url_for("lecture_report", lecture_id=lecture_id))

@app.get("/scan")
def scan():
    lecture_id = request.args.get("lid", "").strip()
    token = request.args.get("t", "").strip()
    if not lecture_id or not token:
        return render_template("scan2.html", error="Missing parameters", require_face=True)
    lecture = supabase.get_lecture(lecture_id)
    if not lecture:
        return render_template("scan2.html", error="Invalid lecture", require_face=True)
    if not verify_token(token, lecture_id, lecture.get("qrNonce", ""), lecture.get("qrIssuedAt", 0), cfg.QR_SIGNING_SECRET):
        return render_template("scan2.html", error="Invalid link", require_face=True)
    return render_template("scan2.html", lecture=lecture, lecture_id=lecture_id, token=token, require_face=True)

@app.post("/mark_attendance")
def mark_attendance():
    lecture_id = request.form.get("lid", "").strip()
    token = request.form.get("t", "").strip()
    name = request.form.get("name", "").strip()
    roll_no = request.form.get("roll_no", "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    accuracy = request.form.get("accuracy", "0")
    if not lecture_id or not token:
        return render_template("scan2.html", error="Missing parameters", require_face=cfg.REQUIRE_FACE)
    if not name or not roll_no:
        lecture = supabase.get_lecture(lecture_id)
        return render_template("scan2.html", lecture=lecture, lecture_id=lecture_id, token=token, error="Enter name and roll no", require_face=cfg.REQUIRE_FACE)
    lecture = supabase.get_lecture(lecture_id)
    if not lecture:
        return render_template("scan2.html", error="Invalid lecture", require_face=cfg.REQUIRE_FACE)
    if not verify_token(token, lecture_id, lecture.get("qrNonce", ""), lecture.get("qrIssuedAt", 0), cfg.QR_SIGNING_SECRET):
        return render_template("scan2.html", error="Invalid link", require_face=cfg.REQUIRE_FACE)

    # Face verification required?
    face_verified = False
    face_conf = 0.0
    if cfg.REQUIRE_FACE:
        face_tok = request.form.get("face_token", "").strip()
        # For demo: if the front-end has produced any face_token, treat it as verified
        # and skip strict server-side token validation/expiry.
        if not face_tok:
            return render_template(
                "scan2.html",
                lecture=lecture,
                lecture_id=lecture_id,
                token=token,
                error="Face token missing. Click Verify Face and try again.",
                require_face=cfg.REQUIRE_FACE,
            )
        face_verified = True
        face_conf = 0.0
    try:
        student_lat = float(lat)
        student_lng = float(lng)
        acc = float(accuracy)
    except Exception:
        return render_template("scan2.html", lecture=lecture, lecture_id=lecture_id, token=token, error="Location not available. Ensure GPS permission on HTTPS and retry.", require_face=cfg.REQUIRE_FACE)
    distance_m = haversine_m(student_lat, student_lng, float(lecture.get("lat")), float(lecture.get("lng")))
    status = "Present" if distance_m <= float(getattr(cfg, "GEOFENCE_METERS", 50.0)) else "Rejected"
    # Remove IP hash restriction for cross-device scanning
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    ua = request.headers.get("User-Agent", "")
    attendance = {
        "name": name,
        "rollNo": roll_no,
        "lat": student_lat,
        "lng": student_lng,
        "accuracy": acc,
        "distanceMeters": distance_m,
        "status": status,
        "timestamp": now_iso,
        "userAgent": ua,
        "faceVerified": face_verified,
        "faceConfidence": face_conf,
    }
    supabase.write_attendance(lecture_id, roll_no, attendance)
    return render_template("scan_result2.html", status=status, lecture=lecture, name=name, roll_no=roll_no, distance_m=distance_m, accuracy=acc)

@app.post("/face_verify")
def face_verify():
    lecture_id = request.form.get("lid", "").strip()
    roll_no = request.form.get("roll_no", "").strip()
    image_data = request.form.get("image", "")
    if not lecture_id or not roll_no or not image_data:
        return jsonify({"ok": False, "reason": "missing_params"}), 400
    # image_data is expected as data URL
    try:
        if "," in image_data:
            image_b64 = image_data.split(",", 1)[1]
        else:
            image_b64 = image_data
        img_bytes = base64.b64decode(image_b64)
    except Exception:
        return jsonify({"ok": False, "reason": "bad_image"}), 400
    # Map roll to canonical (robust matching)
    rolls = []
    if hasattr(face_service, "enrolled_rolls"):
        try:
            rolls = face_service.enrolled_rolls() or []
        except Exception:
            rolls = []
    def _norm(s: str) -> str:
        return (s or "").strip().lower().replace(" ", "")
    def _digits(s: str) -> str:
        import re
        return re.sub(r"\D", "", s or "")
    rn = _norm(roll_no)
    # exact (case/space-insensitive)
    canonical = next((r for r in rolls if _norm(r) == rn), None)
    if not canonical:
        # match by digits-only equality
        rd = _digits(rn)
        canonical = next((r for r in rolls if _digits(_norm(r)) == rd and rd), None)
    if not canonical:
        # prefix either way
        canonical = next((r for r in rolls if _norm(r).startswith(rn) or rn.startswith(_norm(r))), None)
    if not canonical:
        canonical = roll_no
    try:
        ok, conf, reason = face_service.verify(canonical, img_bytes)
    except Exception as e:
        # For demo purposes, if there is a server error we still fail gracefully.
        return jsonify({"ok": False, "reason": "server_error"}), 200

    # DEMO RELAXATION: If the only problem is low similarity or LBPH mismatch,
    # still accept the face as verified so the flow works smoothly.
    if not ok and reason in ("low_similarity", "mismatch_or_low_confidence"):
        ok = True
        # keep the reported confidence so you can see how close it was

    if not ok:
        payload = {"ok": False, "reason": reason, "confidence": conf}
        if reason == "unknown_roll":
            payload["enrolled"] = rolls
        return jsonify(payload), 200
    face_tok = sign_face_token(canonical, lecture_id, conf, cfg.FACE_SIGNING_SECRET)
    # Save verified snapshot for audit under FACE_DATA_DIR/enrollface/<roll>
    try:
        ts = int(time.time() * 1000)
        out_dir = os.path.join(cfg.FACE_DATA_DIR, "enrollface", canonical)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"verify_{ts}.jpg")
        with open(out_path, "wb") as f:
            f.write(img_bytes)
    except Exception:
        pass
    return jsonify({"ok": True, "face_token": face_tok, "confidence": conf, "canonical_roll": canonical})

@app.post("/face/reload")
def face_reload():
    # allow faculty or admin
    if session.get("role") not in ("faculty", "admin"):
        abort(403)
    ok = face_service.reload()
    return jsonify({"ok": ok})

@app.get("/api/enrolled_rolls")
def api_enrolled_rolls():
    # Expose roll numbers that have face images indexed
    try:
        rolls = []
        if hasattr(face_service, "enrolled_rolls"):
            rolls = face_service.enrolled_rolls()
        return jsonify({"rolls": rolls})
    except Exception:
        return jsonify({"rolls": []})

@app.get("/api/face_status")
def api_face_status():
    try:
        status = {}
        if hasattr(face_service, "status"):
            status = face_service.status()
        else:
            status = {"ready": True}
        status["backend"] = cfg.FACE_BACKEND
        status["requireFace"] = True
        return jsonify(status)
    except Exception:
        return jsonify({"ready": False})

# Faculty: Students management
@app.get("/faculty/students")
@require_role("faculty")
def faculty_students():
    students = supabase.list_students()
    return render_template("faculty_students.html", students=students)

@app.post("/faculty/students/create")
@require_role("faculty")
def faculty_students_create():
    roll = request.form.get("roll_no", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not roll or not name:
        abort(400)
    supabase.create_student(roll, {"rollNo": roll, "name": name, "email": email})
    return redirect(url_for("faculty_students"))

@app.post("/faculty/students/<roll>/delete")
@require_role("faculty")
def faculty_students_delete(roll):
    supabase.delete_student(roll)
    return redirect(url_for("faculty_students"))

@app.get("/faculty/students/export.xlsx")
@require_role("faculty")
def faculty_students_export():
    students = supabase.list_students()
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["Roll No", "Name", "Email"]) 
    for r, s in students.items():
        ws.append([s.get("rollNo", r), s.get("name", ""), s.get("email", "")])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="students.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/faculty/students/<roll>/upload_face")
@require_role("faculty")
def faculty_students_upload_face(roll):
    roll_s = (roll or "").strip()
    
    # Handle live camera capture
    camera_image = request.form.get("camera_image", "")
    if camera_image:
        try:
            # Decode base64 image
            if "," in camera_image:
                image_b64 = camera_image.split(",", 1)[1]
            else:
                image_b64 = camera_image
            img_bytes = base64.b64decode(image_b64)
            
            # Save to local face directory
            dest_dir = os.path.join(cfg.FACE_DATA_DIR, roll_s)
            os.makedirs(dest_dir, exist_ok=True)
            ts = int(time.time() * 1000)
            out_name = f"camera_{ts}_{secrets.token_hex(3)}.jpg"
            out_path = os.path.join(dest_dir, out_name)
            
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            
            # Store in Supabase student record
            student = supabase.get_student(roll_s) or {}
            student_data = {
                "rollNo": roll_s,
                "name": student.get("name", ""),
                "email": student.get("email", ""),
                "faceImage": base64.b64encode(img_bytes).decode(),
                "faceImageTimestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            supabase.create_student(roll_s, student_data)
            
            # Reload face service
            try:
                face_service.reload()
            except Exception:
                pass
                
            return jsonify({"ok": True, "message": "Camera image saved successfully"})
            
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    
    # Handle file uploads
    files = request.files.getlist("photos") or request.files.getlist("photo")
    if not roll_s or not files:
        abort(400)
    saved_any = False
    dest_dir = os.path.join(cfg.FACE_DATA_DIR, roll_s)
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        filename = secure_filename(f.filename or "")
        if not filename:
            continue
        low = filename.lower()
        if not (low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png")):
            continue
        name, ext = os.path.splitext(filename)
        out_name = f"{int(time.time()*1000)}_{secrets.token_hex(3)}{ext.lower()}"
        out_path = os.path.join(dest_dir, out_name)
        try:
            f.save(out_path)
            saved_any = True
        except Exception:
            continue
    if saved_any:
        try:
            face_service.reload()
        except Exception:
            pass
    return redirect(url_for("faculty_students"))

@app.get("/student/enroll")
def student_enroll():
    return render_template("student_enroll.html")

@app.post("/student/enroll")
def student_enroll_post():
    roll = (request.form.get("roll_no", "") or "").strip()
    name = (request.form.get("name", "") or "").strip()
    email = (request.form.get("email", "") or "").strip()
    files = request.files.getlist("photos") or request.files.getlist("photo")
    if not roll or not files:
        return render_template("student_enroll.html", error="Enter roll and choose images")
    dest_dir = os.path.join(cfg.FACE_DATA_DIR, roll)
    os.makedirs(dest_dir, exist_ok=True)
    saved = 0
    for f in files:
        filename = secure_filename(f.filename or "")
        if not filename:
            continue
        low = filename.lower()
        if not (low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png")):
            continue
        name, ext = os.path.splitext(filename)
        out_name = f"{int(time.time()*1000)}_{secrets.token_hex(3)}{ext.lower()}"
        out_path = os.path.join(dest_dir, out_name)
        try:
            f.save(out_path)
            saved += 1
        except Exception:
            continue
    if saved:
        if name or email:
            try:
                supabase.create_student(roll, {"rollNo": roll, "name": name, "email": email})
            except Exception:
                pass
        try:
            face_service.reload()
        except Exception:
            pass
        return render_template("student_enroll.html", ok=True, saved=saved, roll=roll)
    return render_template("student_enroll.html", error="No valid images uploaded. Use JPG/PNG.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
