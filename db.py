from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config.update(
    MYSQL_HOST='localhost',
    MYSQL_USER='root',
    MYSQL_PASSWORD='Faisal@2003', #enter your batabase password
    MYSQL_DB='clinic_db'
)
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/patients')
def show_patients():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM patient")
    patients = cur.fetchall()
    cur.close()
    return render_template('show_patients.html', patients=patients)

@app.route('/patients/new', methods=['GET', 'POST'])
def new_patient():
    if request.method == 'POST':
        cid = request.form['cid']
        name = request.form['name']
        gender = request.form['gender']
        contact = request.form['contact']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO patient (CID, Name, Gender, ContactNumber) VALUES (%s, %s, %s, %s)",
            (cid, name, gender, contact)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('show_patients'))
    return render_template('new_patient.html')

@app.route('/patients/delete/<cid>', methods=['POST'])
def delete_patient(cid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM patient WHERE CID = %s", (cid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('show_patients'))

@app.route('/appointments')
def show_appointments():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.AppID, p.CID, p.Name, d.Name, a.DateTime, a.Status
        FROM appointment a
        JOIN patient p ON a.PID = p.PID
        JOIN doctor d ON a.DID = d.DID
    """)
    appointments = cur.fetchall()
    cur.close()
    return render_template('show_appointments.html', appointments=appointments)

@app.route('/appointments/new', methods=['GET', 'POST'])
def make_appointment():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        cid = request.form['cid']
        did = request.form['did']
        dt = request.form['datetime']

        cur.execute("SELECT PID FROM patient WHERE CID = %s", (cid,))
        result = cur.fetchone()
        if result:
            pid = result[0]
            cur.execute(
                "INSERT INTO appointment (PID, DID, DateTime, Status) VALUES (%s, %s, %s, %s)",
                (pid, did, dt, "Scheduled")
            )
            mysql.connection.commit()
        cur.close()
        return redirect(url_for('show_appointments'))

    cur.execute("SELECT DID, Name FROM doctor")
    doctors = cur.fetchall()
    cur.close()
    return render_template('make_appointment.html', doctors=doctors)

# New route to cancel appointment by updating status only
@app.route('/appointments/cancel/<int:app_id>', methods=['POST'])
def cancel_appointment(app_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE appointment SET Status = %s WHERE AppID = %s", ("Canceled", app_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('show_appointments'))

@app.route('/report/new', methods=['GET', 'POST'])
def add_report():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        app_id = request.form['app_id']
        code = request.form['diagnosis_code']
        desc = request.form['description']

        cur.execute(
            "INSERT INTO report (AppID, DiagnosisCode, Description) VALUES (%s, %s, %s)",
            (app_id, code, desc)
        )
        # Mark appointment as Completed after report submission
        cur.execute(
            "UPDATE appointment SET Status = %s WHERE AppID = %s",
            ("Completed", app_id)
        )
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))

    cur.execute("""
        SELECT a.AppID, p.Name AS PatientName, d.Name AS DoctorName, a.DateTime
        FROM appointment a
        JOIN patient p ON a.PID = p.PID
        JOIN doctor d ON a.DID = d.DID
        WHERE a.Status = 'Scheduled'
    """)
    appointments = cur.fetchall()

    cur.execute("SELECT DiagnosisCode, DiagnosisName FROM diagnoses")
    diagnoses = cur.fetchall()
    cur.close()
    return render_template('add_report.html', appointments=appointments, diagnoses=diagnoses)

@app.route('/reports')
def show_reports():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.ReportID, r.DiagnosisCode, r.Description, 
               a.AppID, p.Name AS PatientName, d.Name AS DoctorName, a.DateTime
        FROM report r
        JOIN appointment a ON r.AppID = a.AppID
        JOIN patient p ON a.PID = p.PID
        JOIN doctor d ON a.DID = d.DID
    """)
    reports = cur.fetchall()
    cur.close()
    return render_template('show_reports.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)
