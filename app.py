from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import dbhelper
import os
from werkzeug.utils import secure_filename
import pytz

app = Flask(__name__)
app.secret_key = "Cedric@#123"

app.config["UPLOAD_FOLDER"] = "static/uploads"  # Corrected filepath for profile images
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_profile", methods=["POST"])
def upload_profile():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if "profile_pic" not in request.files:
        flash("No file selected!", "danger")
        return redirect(url_for("edit"))

    file = request.files["profile_pic"]
    
    if file.filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("edit"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        dbhelper.update_profile_picture(session["user"], filename)
        flash("Profile picture updated successfully!", "success")
    
    return redirect(url_for("edit"))

@app.route("/")
def index():
    if "user" in session:
        return redirect("/dashboard")
    flash("Please log in to continue.", "info")
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "register" in request.form:  # User Registration
            idno = request.form["idno"]
            lastname = request.form["lastname"]
            firstname = request.form["firstname"]
            middlename = request.form["middlename"]
            course = request.form["course"]
            year_level = request.form["year_level"]
            email = request.form["email"]
            username = request.form["username"]
            password = request.form["password"]

            if dbhelper.register_user(idno, lastname, firstname, middlename, course, year_level, email, username, password):
                flash("Registration Successful! Please log in.", "success")
                return redirect(url_for("login"))
            else:
                flash("Username already exists! Try another.", "danger")

        else:  # User Login
            username = request.form["username"]
            password = request.form["password"]

            user_type = dbhelper.validate_user(username, password)

            if user_type == "admin":
                session["user"] = username
                flash("Admin Login Successful!", "success")
                return redirect(url_for("admin_dashboard"))  # Redirect admin

            elif user_type == "user":
                session["user"] = username
                user_info = dbhelper.get_user_info(username)
                if user_info:
                    flash("Login Successful!", "success")
                    return redirect(url_for("dashboard"))  

            else:
                flash("Invalid credentials! Try again.", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    user_info = dbhelper.get_user_info(session["user"])
    announcements = dbhelper.get_announcements()
    if user_info:
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8]
        }
        return render_template("dashboard.html", pagetitle="Dashboard", user=user_data, announcements=announcements)

    flash("User not found!", "danger")
    return redirect(url_for('login'))

@app.route("/profile")
def profile():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    user_info = dbhelper.get_user_info(session["user"])
    
    if user_info:
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8]
        }
        return render_template("profile.html", pagetitle="Profile" , user=user_data)
    
    flash("User not found!", "danger")
    return redirect(url_for('dashboard'))

@app.route("/announcement")
def announcement():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    announcements = dbhelper.get_announcements()
    return render_template("announcement.html", pagetitle="Announcement", announcements=announcements)

@app.route("/announcement", methods=["POST"])
def post_announcement():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    announcement_detail = request.form.get("announcement")
    if not announcement_detail:
        flash("Announcement cannot be empty!", "danger")
        return redirect(url_for("admin_dashboard"))

    admin_id = dbhelper.get_admin_id(session["user"])
    if not admin_id:
        flash("Admin ID not found. Please check your account.", "danger")
        return redirect(url_for("admin_dashboard"))

    if dbhelper.insert_announcement(announcement_detail, admin_id):
        flash("Announcement posted successfully!", "success")
    else:
        flash("Failed to post announcement. Try again.", "danger")

    return redirect(url_for("admin_dashboard"))

@app.route("/activate_announcement/<int:announcement_id>", methods=["POST"])
def activate_announcement(announcement_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if dbhelper.update_announcement_status(announcement_id, "active"):
        flash("Announcement activated successfully!", "success")
    else:
        flash("Failed to activate announcement. Try again.", "danger")

    return redirect(url_for("admin_dashboard"))

@app.route("/deactivate_announcement/<int:announcement_id>", methods=["POST"])
def deactivate_announcement(announcement_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if dbhelper.update_announcement_status(announcement_id, "inactive"):
        flash("Announcement deactivated successfully!", "success")
    else:
        flash("Failed to deactivate announcement. Try again.", "danger")

    return redirect(url_for("admin_dashboard"))

@app.route("/delete_announcement/<int:announcement_id>", methods=["POST"])
def delete_announcement(announcement_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if dbhelper.delete_announcement(announcement_id):
        flash("Announcement deleted successfully!", "success")
    else:
        flash("Failed to delete announcement. Try again.", "danger")

    return redirect(url_for("admin_dashboard"))

@app.route("/rules")
def rules():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    return render_template("rules.html", pagetitle="Rules")

@app.route("/history", methods=["GET", "POST"])
def history_feedback():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    # Fetch student ID from the session
    user_info = dbhelper.get_user_info(session["user"])
    if user_info:
        student_id = user_info[0]
        sit_in_records = dbhelper.get_sit_in_history(student_id)

        # Fetch login_time and logout_time for each sit_in record
        for record in sit_in_records:
            record['login_time'] = record['login_time']
            record['logout_time'] = record['logout_time']
    else:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        lab_number = request.form.get('lab_number')
        message = request.form.get('message')
        rating = request.form.get('rating')  # Get the rating from the form
        login_time = request.form.get('login_time')
        logout_time = request.form.get('logout_time')

        if not lab_number or not message or not rating or not login_time or not logout_time:
            flash("Please fill out all fields!", "danger")      
        else:
            success = dbhelper.insert_feedback(student_id, lab_number, message, int(rating), login_time, logout_time)
            if success:
                flash("Feedback submitted successfully!", "success")   
                return redirect(url_for("history_feedback"))
            else:
                flash("Failed to submit feedback. Try again.", "danger")

    return render_template("history.html", pagetitle="Sit-in History", sit_in_records=sit_in_records, student_id=student_id)

@app.route("/reservation", methods=["GET", "POST"])
def reservation():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    user_info = dbhelper.get_user_info(session["user"])
    if request.method == "POST":
        student_id = request.form["student_id"]
        full_name = request.form["full_name"]
        purpose = request.form["subject"]
        lab_number = request.form["room"]
        pc_number = request.form["pc"]
        date = request.form["date"]
        time_in = request.form["time_in"]

        # Insert reservation into the database
        success = dbhelper.insert_reservation(student_id, full_name, purpose, lab_number, pc_number, date, time_in)
        if success:
            flash("Reservation successful!", "success")
        else:
            flash("Failed to make a reservation. Please try again.", "danger")

        return redirect(url_for("reservation"))

    if user_info:
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8]
        }
        return render_template("reservation.html", pagetitle="Reservation", user=user_data)

    flash("User not found!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/view_feedback")
def view_feedback():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    feedbacks = dbhelper.get_feedbacks()
    return render_template("feedback_report.html", pagetitle="Feedback Reports", feedbacks=feedbacks)
  

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        lastname = request.form["lastname"]
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        course = request.form["course"]
        year_level = request.form["year_level"]
        email = request.form["email"]

        dbhelper.update_user_info(session["user"], lastname, firstname, middlename, course, year_level, email)
        flash("Your information has been updated successfully!", "success")
        return redirect(url_for("profile"))

    user_info = dbhelper.get_user_info(session["user"])

    if user_info:
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",  
            "session": user_info[8] 
        }
        return render_template("edit.html", pagetitle="Edit Information", user=user_data)

    flash("User not found!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    if "user" in session:
        user_info = dbhelper.get_user_info(session["user"])
        session.pop("user", None)
        flash("You have been logged out!", "info")
    return redirect(url_for('login'))

@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    total_students = dbhelper.total_students()
    total_feedback = dbhelper.total_feedback()
    total_sit_in = dbhelper.total_sit_in()
    total_reservations = dbhelper.get_total_reservations()  # Add this line
    announcements = dbhelper.get_announcements(include_inactive=True)
    purpose_counts = dbhelper.get_purpose_counts()
    leaderboard = dbhelper.get_leaderboard()

    # Add rank to leaderboard data
    for rank, student in enumerate(leaderboard, start=1):
        student["rank"] = rank

    return render_template(
        "admin_dashboard.html",
        pagetitle="Admin Dashboard",
        total_students=total_students,
        announcements=announcements,
        total_feedback=total_feedback,
        purpose_counts=purpose_counts,
        total_sit_in=total_sit_in,
        total_reservations=total_reservations,  # Pass it to the template
        leaderboard=leaderboard
    )

@app.route("/view_students", methods=['GET', 'POST'])
def view_students():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    students = dbhelper.get_students()
    student = None
    if request.method == 'POST':
        idno = request.form['idno']
        student = dbhelper.search_student_by_id(idno)
        if not student:
            flash('Student not found', 'danger')
    return render_template("students.html", pagetitle="View Students", students=students, student=student)

@app.route("/view_sit_in")
def view_sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    search = request.args.get('search', '')
    sit_in_records = dbhelper.get_all_sit_in_records(search)
    purpose_counts = dbhelper.get_purpose_counts()
    lab_counts = dbhelper.get_lab_counts()
    return render_template("view_sit_in.html", pagetitle="View Sit-in Records", sit_in_records=sit_in_records, purpose_counts=purpose_counts, lab_counts=lab_counts)

@app.route('/submit_sit_in', methods=['POST'])
def submit_sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    idno = request.form['idno']
    purpose = request.form['purpose']
    lab = request.form['lab']

    if dbhelper.insert_sit_in(idno, purpose, lab):  
        dbhelper.decrement_session(idno)
        flash("Sit-In recorded successfully!", "success")
    else:
        flash("Failed to record Sit-In. Try again.", "danger")

    return redirect(url_for('view_students'))

@app.route('/sit_in', methods=['GET'])
def sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 10

    sit_ins, total_pages = dbhelper.get_sit_ins(search, page, per_page)

    return render_template('sit_in.html', sit_ins=sit_ins, page=page, total_pages=total_pages, pagetitle="Current Sit-in")

@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    if "user" not in session:
        return {"success": False, "message": "You need to log in first!"}

    if dbhelper.reset_all_sessions():
        return {"success": True}
    else:
        return {"success": False, "message": "Failed to reset sessions."}

@app.route('/insert_sit_in', methods=['POST'])
def insert_sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    if request.method == 'POST':
        student_id = request.form['idno']
        purpose = request.form['purpose']
        lab = request.form['lab']
        

        success = dbhelper.insert_sit_in(student_id, purpose, lab)
        
        if success:
            flash('Sit-In entry added successfully!', 'success')
        else:
            flash('Failed to add Sit-In entry.', 'danger')
        
        return redirect(url_for('search_student_page'))

@app.route('/logout_sit_in/<int:idno>', methods=['POST'])
def logout_sit_in(idno):  # Changed parameter name from idno to id
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    dbhelper.update_logout_time(idno)  # Use id instead of idno
    flash("User is logged out!", "success")
    return redirect(url_for('sit_in'))

@app.route('/sit_in_reports', methods=['GET'])
def sit_in_reports():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    date_filter = request.args.get('date', '')
    search_filter = request.args.get('search', '')
    sit_in_records = dbhelper.get_all_sit_in_records_by_date_and_purpose(date_filter, search_filter)

    return render_template("sit_in_reports.html", pagetitle="Generate Reports", sit_in_records=sit_in_records)

@app.route('/reset_session/<int:idno>', methods=['POST'])
def reset_session(idno):
    if "user" not in session:
        return jsonify({"success": False, "message": "You need to log in first!"})

    if dbhelper.reset_session(idno):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Failed to reset session."})

@app.route('/laboratory')
def laboratory():
    return render_template('laboratory.html', pagetitle="Computer Control")

@app.route('/get_pc_status/<lab_number>', methods=['GET'])
def get_pc_status(lab_number):
    pcs = dbhelper.get_pc_statuses(lab_number)  # Fetch PC statuses from the database
    return jsonify({"success": True, "pcs": pcs})

@app.route('/update_pc_status', methods=['POST'])
def update_pc_status():
    data = request.json
    lab_number = data.get('lab_number')
    pc_numbers = data.get('pc_numbers')
    status = data.get('status')

    if not lab_number or not pc_numbers or not status:
        return jsonify({"success": False, "message": "Invalid data!"})

    success = dbhelper.update_pc_statuses(lab_number, pc_numbers, status)  # Update PC statuses in the database
    if success:
        return jsonify({"success": True, "message": "PC statuses updated successfully!"})
    else:
        return jsonify({"success": False, "message": "Failed to update PC statuses!"})

@app.route('/add_points_and_logout/<int:idno>', methods=['POST'])
def add_points_and_logout(idno):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    # Update points and set status to inactive
    dbhelper.add_points_and_logout(idno)
    flash("Points added and logged out!", "success")
    return redirect(url_for('sit_in'))

@app.route("/reservations", methods=["GET", "POST"])
def reservations():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    reservations = dbhelper.get_reservations()

    if request.method == "POST":
        reservation_id = request.form["reservation_id"]
        action = request.form["action"]
        admin_id = dbhelper.get_admin_id(session["user"])

        if dbhelper.update_reservation_status(reservation_id, action, admin_id):
            if action == "approved":
                flash("Reservation approved and PC status updated to 'used'!", "success")
            else:
                flash("Reservation disapproved!", "success")
        else:
            flash("Failed to update reservation status. Try again.", "danger")

        return redirect(url_for("reservations"))

    return render_template("admin_reservation.html", pagetitle="Reservations", reservations=reservations)

@app.route("/logs")
def logs():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    logs = dbhelper.get_logs()
    return render_template("logs.html", pagetitle="Logs", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)