from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import get_db_connection
from reportlab.pdfgen import canvas
from flask import Flask, render_template, request, redirect, url_for
import io
import csv
import openai

app = Flask(__name__)
app.secret_key = "iot_secret_key"

openai.api_key = "YOUR_OPENAI_API_KEY"

# ------------------- LOGIN --------------------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id,name,role,password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[2]
            return redirect(f"/{user[2]}_dashboard")
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

# ------------------- REGISTRATION --------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                       (name,email,password,role))
        db.commit()
        db.close()
        return redirect('/login')
    return render_template('register.html')

# ------------------- DASHBOARDS --------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    total_patients = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    total_doctors = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM health_data")
    total_data = cur.fetchone()[0]

    cur.execute("""
        SELECT u.id, u.name, u.email, u.assigned_doctor_id, d.name as doctor_name
        FROM users u LEFT JOIN users d ON u.assigned_doctor_id = d.id
        WHERE u.role='patient'
    """)
    patients_list = cur.fetchall()

    cur.execute("SELECT id, name, email FROM users WHERE role='doctor'")
    doctors_list = cur.fetchall()

    cur.execute("""
        SELECT u.name,h.heart_rate,h.spo2,h.temperature,h.timestamp
        FROM health_data h JOIN users u ON h.patient_id=u.id
        ORDER BY h.timestamp DESC LIMIT 10
    """)
    health_data = cur.fetchall()

    db.close()
    return render_template('dashboard_admin.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_devices=total_data,
                           health_data=health_data,
                           patients_list=patients_list,
                           doctors_list=doctors_list)

@app.route('/admin/doctors')
def manage_doctors():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE role='doctor'")
    doctors_list = cur.fetchall()
    db.close()
    return render_template('manage_doctors.html', doctors_list=doctors_list)

@app.route('/admin/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'doctor')",
                    (name, email, password))
        db.commit()
        db.close()
        return redirect('/admin/doctors')
    return render_template('add_doctor.html')

@app.route('/admin/doctors/edit/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        cur.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (name, email, doctor_id))
        db.commit()
        db.close()
        return redirect('/admin/doctors')
    cur.execute("SELECT id, name, email FROM users WHERE id=%s", (doctor_id,))
    doctor = cur.fetchone()
    db.close()
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/admin/doctors/delete/<int:doctor_id>')
def delete_doctor(doctor_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (doctor_id,))
    db.commit()
    db.close()
    return redirect('/admin/doctors')




@app.route('/admin/patients')
def manage_patients():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT u.id, u.name, u.email, d.name as doctor_name
        FROM users u LEFT JOIN users d ON u.assigned_doctor_id = d.id
        WHERE u.role='patient'
    """)
    patients_list = cur.fetchall()
    db.close()
    return render_template('manage_patients.html', patients_list=patients_list)

@app.route('/admin/patients/add', methods=['GET', 'POST'])
def add_patient():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'patient')",
                    (name, email, password))
        db.commit()
        db.close()
        return redirect('/admin/patients')
    return render_template('add_patient.html')

@app.route('/admin/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        doctor_id = request.form['doctor_id']
        cur.execute("UPDATE users SET name=%s, email=%s, assigned_doctor_id=%s WHERE id=%s",
                    (name, email, doctor_id, patient_id))
        db.commit()
        db.close()
        return redirect('/admin/patients')
    cur.execute("SELECT id, name, email, assigned_doctor_id FROM users WHERE id=%s", (patient_id,))
    patient = cur.fetchone()
    cur.execute("SELECT id, name FROM users WHERE role='doctor'")
    doctors = cur.fetchall()
    db.close()
    return render_template('edit_patient.html', patient=patient, doctors=doctors)

@app.route('/admin/patients/delete/<int:patient_id>')
def delete_patient(patient_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (patient_id,))
    db.commit()
    db.close()
    return redirect('/admin/patients')

@app.route('/admin/devices')
def manage_devices():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT d.id, d.device_id, u.name as patient_name, d.status, d.last_upload
        FROM devices d LEFT JOIN users u ON d.patient_id = u.id
    """)
    devices_list = cur.fetchall()
    db.close()
    return render_template('manage_devices.html', devices_list=devices_list)

@app.route('/admin/devices/add', methods=['GET', 'POST'])
def add_device():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        device_id = request.form['device_id']
        db = get_db_connection()
        cur = db.cursor()
        cur.execute("INSERT INTO devices (device_id) VALUES (%s)", (device_id,))
        db.commit()
        db.close()
        return redirect('/admin/devices')
    return render_template('add_device.html')

@app.route('/admin/devices/edit/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        cur.execute("UPDATE devices SET patient_id=%s WHERE id=%s", (patient_id, device_id))
        db.commit()
        db.close()
        return redirect('/admin/devices')
    cur.execute("SELECT id, device_id, patient_id FROM devices WHERE id=%s", (device_id,))
    device = cur.fetchone()
    cur.execute("SELECT id, name FROM users WHERE role='patient'")
    patients = cur.fetchall()
    db.close()
    return render_template('edit_device.html', device=device, patients=patients)

@app.route('/admin/devices/delete/<int:device_id>')
def delete_device(device_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM devices WHERE id=%s", (device_id,))
    db.commit()
    db.close()
    return redirect('/admin/devices')




@app.route('/admin/health_data')
def health_data():
    if session.get('role') != 'admin':
        return redirect('/login')

    patient_filter = request.args.get('patient')
    doctor_filter = request.args.get('doctor')
    date_filter = request.args.get('date')

    db = get_db_connection()
    cur = db.cursor()

    query = """
        SELECT u.name, h.temperature, h.heart_rate, h.spo2, h.bp, h.timestamp
        FROM health_data h JOIN users u ON h.patient_id = u.id
        LEFT JOIN users d ON u.assigned_doctor_id = d.id
    """
    filters = []
    params = []

    if patient_filter:
        filters.append("u.name LIKE %s")
        params.append(f"%{patient_filter}%")
    if doctor_filter:
        filters.append("d.name LIKE %s")
        params.append(f"%{doctor_filter}%")
    if date_filter:
        filters.append("DATE(h.timestamp) = %s")
        params.append(date_filter)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY h.timestamp DESC"

    cur.execute(query, tuple(params))
    health_data_list = cur.fetchall()
    db.close()

    return render_template('health_data.html',
                           health_data_list=health_data_list,
                           patient_filter=patient_filter,
                           doctor_filter=doctor_filter,
                           date_filter=date_filter)

@app.route('/admin/health_data/export/csv')
def export_health_data_csv():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT u.name, h.temperature, h.heart_rate, h.spo2, h.bp, h.timestamp
        FROM health_data h JOIN users u ON h.patient_id = u.id
        ORDER BY h.timestamp DESC
    """)
    health_data_list = cur.fetchall()
    db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient', 'Temperature', 'Heart Rate', 'SpO2', 'Blood Pressure', 'Timestamp'])
    for row in health_data_list:
        writer.writerow(row)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='health_data.csv')

@app.route('/admin/health_data/export/pdf')
def export_health_data_pdf():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT u.name, h.temperature, h.heart_rate, h.spo2, h.bp, h.timestamp
        FROM health_data h JOIN users u ON h.patient_id = u.id
        ORDER BY h.timestamp DESC
    """)
    health_data_list = cur.fetchall()
    db.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "Health Data Report")
    y = 750
    for row in health_data_list:
        p.drawString(100, y, f"Patient: {row[0]}, Temp: {row[1]}, HR: {row[2]}, SpO2: {row[3]}, BP: {row[4]}, Time: {row[5]}")
        y -= 20
    p.save()
    buffer.seek(0)

    return send_file(buffer,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name='health_data.pdf')

@app.route('/admin/ai_suggestions')
def ai_suggestions():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT s.id, u.name, s.suggestion_text, s.verified, s.timestamp
        FROM ai_suggestions s JOIN users u ON s.patient_id = u.id
        ORDER BY s.timestamp DESC
    """)
    suggestions_list = cur.fetchall()
    db.close()
    return render_template('ai_suggestions.html', suggestions_list=suggestions_list)

@app.route('/admin/ai_suggestions/verify/<int:suggestion_id>')
def verify_suggestion(suggestion_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE ai_suggestions SET verified = TRUE WHERE id = %s", (suggestion_id,))
    db.commit()
    db.close()
    return redirect('/admin/ai_suggestions')

@app.route('/admin/ai_suggestions/delete/<int:suggestion_id>')
def delete_suggestion(suggestion_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM ai_suggestions WHERE id = %s", (suggestion_id,))
    db.commit()
    db.close()
    return redirect('/admin/ai_suggestions')

@app.route('/admin/reports')
def reports():
    if session.get('role') != 'admin':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()

    # Patients per doctor
    cur.execute("""
        SELECT d.name, COUNT(p.id)
        FROM users d
        LEFT JOIN users p ON d.id = p.assigned_doctor_id
        WHERE d.role = 'doctor'
        GROUP BY d.name
    """)
    patients_per_doctor = cur.fetchall()

    # Health records per patient
    cur.execute("""
        SELECT u.name, COUNT(h.id)
        FROM users u
        LEFT JOIN health_data h ON u.id = h.patient_id
        WHERE u.role = 'patient'
        GROUP BY u.name
    """)
    records_per_patient = cur.fetchall()

    db.close()
    return render_template('reports.html',
                           patients_per_doctor=patients_per_doctor,
                           records_per_patient=records_per_patient)

@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        site_name = request.form['site_name']
        with open('site_name.txt', 'w') as f:
            f.write(site_name)
        return redirect('/admin/settings')
    try:
        with open('site_name.txt', 'r') as f:
            site_name = f.read()
    except FileNotFoundError:
        site_name = "IoT Health Checker"
    return render_template('settings.html', site_name=site_name)















@app.route('/doctor_dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE assigned_doctor_id=%s", (session['user_id'],))
    total_assigned_patients = cur.fetchone()[0]

    # Placeholder for abnormal vitals alerts
    abnormal_vitals_alerts = 0 # This would require specific logic to determine abnormal ranges

    # Placeholder for latest reports
    latest_reports = 0 # This would require a reports generation feature

    cur.execute("""
        SELECT COUNT(s.id)
        FROM ai_suggestions s
        JOIN users u ON s.patient_id = u.id
        WHERE u.assigned_doctor_id = %s
    """, (session['user_id'],))
    ai_suggestions_count = cur.fetchone()[0]

    cur.execute("""
        SELECT u.name, s.suggestion_text, s.timestamp
        FROM ai_suggestions s
        JOIN users u ON s.patient_id = u.id
        WHERE u.assigned_doctor_id = %s
        ORDER BY s.timestamp DESC LIMIT 5
    """, (session['user_id'],))
    suggestions = cur.fetchall()

    db.close()
    return render_template('dashboard_doctor.html',
                           total_assigned_patients=total_assigned_patients,
                           abnormal_vitals_alerts=abnormal_vitals_alerts,
                           latest_reports=latest_reports,
                           ai_suggestions_count=ai_suggestions_count,
                           suggestions=suggestions)

@app.route('/doctor/patients')
def my_patients():
    if session.get('role') != 'doctor':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT u.id, u.name, u.age, u.gender, d.device_id, d.status,
               h.heart_rate, h.spo2, h.temperature, h.timestamp
        FROM users u
        LEFT JOIN devices d ON u.id = d.patient_id
        LEFT JOIN (
            SELECT h1.patient_id, h1.heart_rate, h1.spo2, h1.temperature, h1.timestamp
            FROM health_data h1
            WHERE h1.id IN (SELECT MAX(id) FROM health_data GROUP BY patient_id)
        ) h ON u.id = h.patient_id
        WHERE u.assigned_doctor_id = %s AND u.role = 'patient'
    """, (session['user_id'],))
    patients_list = cur.fetchall()
    db.close()
    return render_template('my_patients.html', patients_list=patients_list)

@app.route('/doctor/health_data/<int:patient_id>')
def patient_health_data(patient_id):
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()

    # Check if the patient is assigned to the current doctor
    cur.execute("SELECT assigned_doctor_id FROM users WHERE id=%s", (patient_id,))
    assigned_doctor_id = cur.fetchone()[0]
    if assigned_doctor_id != session['user_id']:
        db.close()
        return "Unauthorized", 403 # Or redirect to an error page

    date_filter = request.args.get('date')

    query = """
        SELECT id, temperature, heart_rate, spo2, bp, timestamp
        FROM health_data
        WHERE patient_id = %s
    """
    params = [patient_id]

    if date_filter:
        query += " AND DATE(timestamp) = %s"
        params.append(date_filter)

    query += " ORDER BY timestamp DESC"

    cur.execute(query, tuple(params))
    health_data = cur.fetchall()

    cur.execute("SELECT name FROM users WHERE id=%s", (patient_id,))
    patient_name = cur.fetchone()[0]

    db.close()
    return render_template('patient_health_data.html',
                           patient_name=patient_name,
                           health_data=health_data,
                           patient_id=patient_id,
                           date_filter=date_filter)

@app.route('/doctor/health_data/add/<int:patient_id>', methods=['GET', 'POST'])
def add_health_data(patient_id):
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT assigned_doctor_id FROM users WHERE id=%s", (patient_id,))
    assigned_doctor_id = cur.fetchone()[0]
    if assigned_doctor_id != session['user_id']:
        db.close()
        return "Unauthorized", 403

    if request.method == 'POST':
        temperature = request.form['temperature']
        heart_rate = request.form['heart_rate']
        spo2 = request.form['spo2']
        bp = request.form['bp']
        cur.execute("""
            INSERT INTO health_data (patient_id, temperature, heart_rate, spo2, bp)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, temperature, heart_rate, spo2, bp))
        db.commit()
        db.close()
        return redirect(url_for('patient_health_data', patient_id=patient_id))

    cur.execute("SELECT name FROM users WHERE id=%s", (patient_id,))
    patient_name = cur.fetchone()[0]
    db.close()
    return render_template('add_health_data.html', patient_name=patient_name, patient_id=patient_id)

@app.route('/doctor/health_data/edit/<int:health_data_id>', methods=['GET', 'POST'])
def edit_health_data(health_data_id):
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()

    if request.method == 'POST':
        temperature = request.form['temperature']
        heart_rate = request.form['heart_rate']
        spo2 = request.form['spo2']
        bp = request.form['bp']
        cur.execute("""
            UPDATE health_data
            SET temperature=%s, heart_rate=%s, spo2=%s, bp=%s
            WHERE id=%s
        """, (temperature, heart_rate, spo2, bp, health_data_id))
        db.commit()
        db.close()
        # Need to get patient_id to redirect back to patient_health_data page
        cur = db.cursor()
        cur.execute("SELECT patient_id FROM health_data WHERE id=%s", (health_data_id,))
        patient_id = cur.fetchone()[0]
        db.close()
        return redirect(url_for('patient_health_data', patient_id=patient_id))

    cur.execute("SELECT id, patient_id, temperature, heart_rate, spo2, bp FROM health_data WHERE id=%s", (health_data_id,))
    health_data_record = cur.fetchone()

    # Check if the patient associated with this health data is assigned to the current doctor
    cur.execute("SELECT assigned_doctor_id FROM users WHERE id=%s", (health_data_record[1],))
    assigned_doctor_id = cur.fetchone()[0]
    if assigned_doctor_id != session['user_id']:
        db.close()
        return "Unauthorized", 403

    db.close()
    return render_template('edit_health_data.html', health_data_record=health_data_record)

@app.route('/doctor/ai_suggestions')
def doctor_ai_suggestions():
    if session.get('role') != 'doctor':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    
    # Fetch Suggestions
    cur.execute("""
        SELECT s.id, u.name, s.suggestion_text, s.verified, s.timestamp, 
               s.doctor_feedback, s.doctor_status, u.id, d.device_id
        FROM ai_suggestions s
        JOIN users u ON s.patient_id = u.id
        LEFT JOIN devices d ON u.id = d.patient_id
        WHERE u.assigned_doctor_id = %s
        ORDER BY s.timestamp DESC
    """, (session['user_id'],))
    suggestions_list = cur.fetchall()
    
    # Fetch Patients for Dropdown
    cur.execute("SELECT id, name FROM users WHERE assigned_doctor_id=%s AND role='patient'", (session['user_id'],))
    my_patients = cur.fetchall()
    
    db.close()
    return render_template('doctor_ai_suggestions.html', suggestions_list=suggestions_list, my_patients=my_patients)

@app.route('/doctor/ai_suggestions/approve/<int:suggestion_id>', methods=['POST'])
def approve_suggestion(suggestion_id):
    if session.get('role') != 'doctor':
        return redirect('/login')
    feedback = request.form.get('feedback', '')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE ai_suggestions SET doctor_status='Approved', doctor_feedback=%s WHERE id=%s", (feedback, suggestion_id))
    db.commit()
    db.close()
    return redirect('/doctor/ai_suggestions')

@app.route('/doctor/ai_suggestions/reject/<int:suggestion_id>', methods=['POST'])
def reject_suggestion(suggestion_id):
    if session.get('role') != 'doctor':
        return redirect('/login')
    feedback = request.form.get('feedback', '')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE ai_suggestions SET doctor_status='Rejected', doctor_feedback=%s WHERE id=%s", (feedback, suggestion_id))
    db.commit()
    db.close()
    return redirect('/doctor/ai_suggestions')

@app.route('/doctor/ai_suggestions/comment/<int:suggestion_id>', methods=['POST'])
def comment_suggestion(suggestion_id):
    if session.get('role') != 'doctor':
        return redirect('/login')
    feedback = request.form.get('feedback', '')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE ai_suggestions SET doctor_feedback=%s WHERE id=%s", (feedback, suggestion_id))
    db.commit()
    db.close()
    return redirect('/doctor/ai_suggestions')

@app.route('/doctor/ai_suggestions/generate', methods=['POST'])
def generate_doctor_ai_suggestion():
    if session.get('role') != 'doctor':
        return redirect('/login')
    
    patient_id = request.form.get('patient_id')
    
    db = get_db_connection()
    cur = db.cursor()
    
    # 1. Fetch latest health data for the patient
    cur.execute("""
        SELECT temperature, heart_rate, spo2, bp 
        FROM health_data 
        WHERE patient_id=%s 
        ORDER BY timestamp DESC LIMIT 1
    """, (patient_id,))
    record = cur.fetchone()
    
    cur.execute("SELECT name FROM users WHERE id=%s", (patient_id,))
    patient_name = cur.fetchone()[0]
    
    db.close()

    if not record:
        # If no data, cannot generate
        # In a real app, flash a message. Here we'll just redirect.
        return redirect('/doctor/ai_suggestions')

    temp, hr, spo2, bp = record
    
    # 2. Generate Suggestion (Mocking OpenAI if key is default)
    suggestion = ""
    
    if openai.api_key == "YOUR_OPENAI_API_KEY":
        # --- MOCK LOGIC ---
        import random
        
        alerts = []
        if hr > 100: alerts.append("Tachycardia detected (HR > 100).")
        if hr < 60: alerts.append("Bradycardia detected (HR < 60).")
        if spo2 < 95: alerts.append(f"Low SpO2 levels ({spo2}%).")
        if temp > 37.5: alerts.append(f"Elevated temperature ({temp}°C).")
        
        if not alerts:
            suggestion = f"Patient {patient_name} appears stable. Vitals are within normal ranges. Continue standard monitoring."
        else:
            base = " ".join(alerts)
            actions = [
                "Recommend immediate nurse check.",
                "Review medication dosage.",
                "Schedule cardiology consult.",
                "Monitor vitals every 15 minutes."
            ]
            suggestion = f"Warning: {base} {random.choice(actions)}"
    else:
        # --- REAL OPENAI CALL ---
        try:
            prompt = f"Patient {patient_name} Vitals: Temp={temp}C, HR={hr}bpm, SpO2={spo2}%, BP={bp}. Analyze for anomalies and suggest brief medical action."
            ai_response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=60
            )
            suggestion = ai_response.choices[0].text.strip()
        except Exception as e:
            suggestion = "Error generating insight. Please check system logs."

    # 3. Save to DB
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("INSERT INTO ai_suggestions (patient_id, suggestion_text, verified) VALUES (%s,%s, FALSE)", (patient_id, suggestion))
    db.commit()
    db.close()

    return redirect('/doctor/ai_suggestions')

@app.route('/doctor/reports')
def doctor_reports():
    if session.get('role') != 'doctor':
        return redirect('/login')
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id, name FROM users WHERE assigned_doctor_id=%s AND role='patient'", (session['user_id'],))
    patients = cur.fetchall()
    db.close()
    return render_template('doctor_reports.html', patients=patients)

@app.route('/doctor/reports/generate/pdf', methods=['GET'])
def generate_doctor_report_pdf():
    if session.get('role') != 'doctor':
        return redirect('/login')

    patient_id = request.args.get('patient_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not patient_id:
        return "Patient ID is required", 400

    db = get_db_connection()
    cur = db.cursor()

    # Verify patient is assigned to doctor
    cur.execute("SELECT assigned_doctor_id FROM users WHERE id=%s AND role='patient'", (patient_id,))
    assigned_doctor_id = cur.fetchone()
    if not assigned_doctor_id or assigned_doctor_id[0] != session['user_id']:
        db.close()
        return "Unauthorized or Patient not assigned to you", 403

    query = """
        SELECT temperature, heart_rate, spo2, bp, timestamp
        FROM health_data
        WHERE patient_id = %s
    """
    params = [patient_id]

    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date)

    query += " ORDER BY timestamp DESC"

    cur.execute(query, tuple(params))
    health_data = cur.fetchall()

    cur.execute("SELECT name FROM users WHERE id=%s", (patient_id,))
    patient_name = cur.fetchone()[0]
    db.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, f"Health Report for {patient_name}")
    p.drawString(100, 780, f"Date Range: {start_date if start_date else 'All'} to {end_date if end_date else 'All'}")

    y = 740
    for r in health_data:
        p.drawString(100, y, f"Temp: {r[0]}°C | HR: {r[1]} bpm | SpO₂: {r[2]}% | BP: {r[3]} | {r[4]}")
        y -= 20
        if y < 50: # New page if content goes too low
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 800

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Health_Report_{patient_name}.pdf", mimetype='application/pdf')

@app.route('/doctor/reports/generate/csv', methods=['GET'])
def generate_doctor_report_csv():
    if session.get('role') != 'doctor':
        return redirect('/login')

    patient_id = request.args.get('patient_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not patient_id:
        return "Patient ID is required", 400

    db = get_db_connection()
    cur = db.cursor()

    # Verify patient is assigned to doctor
    cur.execute("SELECT assigned_doctor_id FROM users WHERE id=%s AND role='patient'", (patient_id,))
    assigned_doctor_id = cur.fetchone()
    if not assigned_doctor_id or assigned_doctor_id[0] != session['user_id']:
        db.close()
        return "Unauthorized or Patient not assigned to you", 403

    query = """
        SELECT temperature, heart_rate, spo2, bp, timestamp
        FROM health_data
        WHERE patient_id = %s
    """
    params = [patient_id]

    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date)

    query += " ORDER BY timestamp DESC"

    cur.execute(query, tuple(params))
    health_data = cur.fetchall()

    cur.execute("SELECT name FROM users WHERE id=%s", (patient_id,))
    patient_name = cur.fetchone()[0]
    db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Temperature', 'Heart Rate', 'SpO2', 'Blood Pressure', 'Timestamp'])
    for row in health_data:
        writer.writerow(row)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name=f"Health_Report_{patient_name}.csv")

@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        specialization = request.form.get('specialization')
        phone_number = request.form.get('phone_number')
        bio = request.form.get('bio')
        accepting_patients = 1 if request.form.get('accepting_patients') == 'on' else 0
        emergency_on_call = 1 if request.form.get('emergency_on_call') == 'on' else 0

        cur.execute("""
            UPDATE users 
            SET name=%s, email=%s, specialization=%s, phone_number=%s, bio=%s, 
                accepting_patients=%s, emergency_on_call=%s
            WHERE id=%s
        """, (name, email, specialization, phone_number, bio, accepting_patients, emergency_on_call, session['user_id']))
        db.commit()
        session['name'] = name # Update session name
        db.close()
        return redirect('/doctor/profile')

    cur.execute("""
        SELECT name, email, specialization, phone_number, bio, accepting_patients, emergency_on_call 
        FROM users WHERE id=%s
    """, (session['user_id'],))
    doctor_info = cur.fetchone()
    
    # Get total patients count for stats
    cur.execute("SELECT COUNT(*) FROM users WHERE assigned_doctor_id=%s AND role='patient'", (session['user_id'],))
    total_patients = cur.fetchone()[0]
    
    db.close()
    return render_template('doctor_profile.html', doctor_info=doctor_info, total_patients=total_patients)

@app.route('/patient_dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        return redirect('/login')
    
    user = {
        'name': session.get('name')
    }

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT temperature,heart_rate,spo2,timestamp FROM health_data WHERE patient_id=%s ORDER BY timestamp DESC LIMIT 1", (session['user_id'],))
    latest = cur.fetchone()

    cur.execute("SELECT suggestion_text FROM ai_suggestions WHERE patient_id=%s ORDER BY timestamp DESC LIMIT 1", (session['user_id'],))
    suggestion = cur.fetchone()

    db.close()
    return render_template('dashboard_patient.html', user=user, latest=latest, suggestion_text=suggestion[0] if suggestion else "No suggestions yet.")

@app.route('/assign_patients', methods=['GET'])
def assign_patients_page():
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE role = 'patient' AND assigned_doctor_id IS NULL")
    unassigned_patients = cur.fetchall()
    db.close()

    return render_template('assign_patients.html', unassigned_patients=unassigned_patients)

@app.route('/assign_patient/<int:patient_id>', methods=['POST'])
def assign_patient(patient_id):
    if session.get('role') != 'doctor':
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("UPDATE users SET assigned_doctor_id = %s WHERE id = %s", (session['user_id'], patient_id))
    db.commit()
    db.close()

    return redirect('/assign_patients')


# ------------------- API --------------------
@app.route('/api/ai_suggestion/<int:patient_id>', methods=['POST'])
def ai_suggestion(patient_id):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT temperature,heart_rate,spo2 FROM health_data WHERE patient_id=%s ORDER BY timestamp DESC LIMIT 1", (patient_id,))
    record = cur.fetchone()
    db.close()

    if not record:
        return jsonify({"error": "No data found"}), 404

    prompt = f"Patient vitals: Temp={record[0]}°C, HR={record[1]} bpm, SpO2={record[2]}%. Give short health advice."
    ai_response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=50
    )

    suggestion = ai_response.choices[0].text.strip()

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("INSERT INTO ai_suggestions (patient_id, suggestion_text) VALUES (%s,%s)", (patient_id, suggestion))
    db.commit()
    db.close()

    return jsonify({"suggestion": suggestion})

@app.route('/api/v1/device/health_data', methods=['POST'])
def device_health_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    device_id = data.get('device_id')
    temperature = data.get('temperature')
    heart_rate = data.get('heart_rate')
    spo2 = data.get('spo2')
    bp = data.get('bp')

    if not all([device_id, temperature, heart_rate, spo2, bp]):
        return jsonify({"error": "Missing data fields"}), 400

    db = get_db_connection()
    cur = db.cursor()

    try:
        # 1. Verify device_id and get patient_id
        cur.execute("SELECT id, patient_id FROM devices WHERE device_id = %s", (device_id,))
        device_info = cur.fetchone()

        if not device_info:
            db.close()
            return jsonify({"error": "Device not found"}), 404

        device_db_id, patient_id = device_info

        if not patient_id:
            db.close()
            return jsonify({"error": "Device not assigned to a patient"}), 403

        # 2. Insert health data
        cur.execute("""
            INSERT INTO health_data (patient_id, temperature, heart_rate, spo2, bp)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, temperature, heart_rate, spo2, bp))

        # 3. Update device last_upload and status
        cur.execute("""
            UPDATE devices
            SET last_upload = CURRENT_TIMESTAMP, status = 'Online'
            WHERE id = %s
        """, (device_db_id,))

        db.commit()
        return jsonify({"message": "Health data received and recorded"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route('/api/doctor/chart_data')
def doctor_chart_data():
    if session.get('role') != 'doctor':
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cur = db.cursor()

    cur.execute("""
        SELECT u.name, h.heart_rate, h.spo2, h.temperature, h.timestamp
        FROM health_data h
        JOIN users u ON h.patient_id = u.id
        WHERE u.assigned_doctor_id = %s
        ORDER BY h.timestamp DESC
        LIMIT 20
    """, (session['user_id'],))
    data = cur.fetchall()
    db.close()

    chart_data = {
        "labels": [row[4].strftime('%Y-%m-%d %H:%M') for row in reversed(data)],
        "datasets": [
            {
                "label": "Heart Rate",
                "data": [row[1] for row in reversed(data)],
                "borderColor": "#1E3A8A",
                "borderWidth": 2,
                "fill": False
            },
            {
                "label": "SpO2",
                "data": [row[2] for row in reversed(data)],
                "borderColor": "#06B6D4",
                "borderWidth": 2,
                "fill": False
            },
            {
                "label": "Temperature",
                "data": [row[3] for row in reversed(data)],
                "borderColor": "#7C3AED",
                "borderWidth": 2,
                "fill": False
            }
        ]
    }
    return jsonify(chart_data)

@app.route('/api/dht11_data', methods=['POST'])
def dht11_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    device_id = data.get('device_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')

    if not all([device_id, temperature, humidity]):
        return jsonify({"error": "Missing data fields"}), 400

    db = get_db_connection()
    cur = db.cursor()

    try:
        # Verify the device exists
        cur.execute("SELECT id FROM devices WHERE device_id = %s", (device_id,))
        device_exists = cur.fetchone()

        if not device_exists:
            db.close()
            return jsonify({"error": "Device not found"}), 404

        # Insert new reading using the string device_id
        cur.execute("""
            INSERT INTO dht11_readings (device_id, temperature, humidity)
            VALUES (%s, %s, %s)
        """, (device_id, temperature, humidity))

        # Update device last_upload and status
        cur.execute("""
            UPDATE devices
            SET last_upload = CURRENT_TIMESTAMP, status = 'Online'
            WHERE device_id = %s
        """, (device_id,))

        db.commit()
        return jsonify({"message": "DHT11 data received and recorded"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/get_latest_dht11_data/<int:patient_id>', methods=['GET'])
def get_latest_dht11_data(patient_id):
    db = get_db_connection()
    cur = db.cursor()

    try:
        # Get the device_id associated with the patient
        cur.execute("SELECT device_id FROM devices WHERE patient_id = %s", (patient_id,))
        device_id_tuple = cur.fetchone()

        if not device_id_tuple:
            return jsonify({"error": "No device assigned to this patient"}), 404
        
        device_id = device_id_tuple[0]

        # Get the latest DHT11 data for this device
        cur.execute("""
            SELECT temperature, humidity, timestamp
            FROM dht11_readings
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id,))
        latest_data = cur.fetchone()

        if not latest_data:
            return jsonify({"error": "No DHT11 data found for this device"}), 404

        temperature, humidity, timestamp = latest_data
        return jsonify({
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/get_historical_dht11_data/<int:patient_id>', methods=['GET'])
def get_historical_dht11_data(patient_id):
    db = get_db_connection()
    cur = db.cursor()

    try:
        # Get the device_id associated with the patient
        cur.execute("SELECT device_id FROM devices WHERE patient_id = %s", (patient_id,))
        device_id_tuple = cur.fetchone()

        if not device_id_tuple:
            return jsonify({"error": "No device assigned to this patient"}), 404
        
        device_id = device_id_tuple[0]

        # Get the latest 20 DHT11 data for this device
        cur.execute("""
            SELECT temperature, humidity, timestamp
            FROM dht11_readings
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 20
        """, (device_id,))
        historical_data = cur.fetchall()

        if not historical_data:
            return jsonify({"error": "No DHT11 data found for this device"}), 404

        
        labels = [row[2].strftime('%Y-%m-%d %H:%M') for row in reversed(historical_data)]
        temperatures = [row[0] for row in reversed(historical_data)]
        humidities = [row[1] for row in reversed(historical_data)]

        chart_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Temperature (°C)",
                    "data": temperatures,
                    "borderColor": "#1E3A8A",
                    "borderWidth": 2,
                    "fill": False
                },
                {
                    "label": "Humidity (%)",
                    "data": humidities,
                    "borderColor": "#06B6D4",
                    "borderWidth": 2,
                    "fill": False
                }
            ]
        }
        return jsonify(chart_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/insert_data', methods=['POST'])
def insert_data():
    patient_id = request.form.get('patient_id')
    temperature = request.form.get('temperature')
    heart_rate = request.form.get('heart_rate')
    spo2 = request.form.get('spo2')
    bp = request.form.get('bp')

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO health_data (patient_id, temperature, heart_rate, spo2, bp)
        VALUES (%s,%s,%s,%s,%s)
    """, (patient_id, temperature, heart_rate, spo2, bp))
    db.commit()
    db.close()
    return "Data Inserted", 200

# ------------------- REPORTING --------------------
@app.route('/download_report')
def download_report():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT temperature,heart_rate,spo2,timestamp
        FROM health_data WHERE patient_id=%s
        ORDER BY timestamp DESC LIMIT 10
    """, (session['user_id'],))
    records = cur.fetchall()
    db.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, f"Health Report for {session['name']}")

    y = 760
    for r in records:
        p.drawString(100, y, f"Temp: {r[0]}°C | HR: {r[1]} bpm | SpO₂: {r[2]}% | {r[3]}")
        y -= 20

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Health_Report.pdf", mimetype='application/pdf')

# ------------------- RUN APP --------------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
