from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_file
import dbhelper
import os
from werkzeug.utils import secure_filename
import pytz
from fpdf import FPDF
import io

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

        # Get notification count
        notification_count = dbhelper.get_unread_notification_count(user_info[0])

        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8],
            "points": user_info[9],
            "notification_count": notification_count
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
        # Get notification count
        notification_count = dbhelper.get_unread_notification_count(user_info[0])
        
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8],
            "points": user_info[9],
            "notification_count": notification_count
        }
        return render_template("profile.html", pagetitle="Profile" , user=user_data)
    
    flash("User not found!", "danger")
    return redirect(url_for('dashboard'))

@app.route("/announcement")
def announcement():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }

    announcements = dbhelper.get_announcements()
    return render_template("announcement.html", pagetitle="Announcement", announcements=announcements, user=user_data)

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
    
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }
    
    return render_template("rules.html", pagetitle="Rules and Regulations", user=user_data)

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

        # Get notification count
        notification_count = dbhelper.get_unread_notification_count(student_id)
        
        # Create user data dictionary for template
        user_data = {
            "idno": user_info[0],
            "lastname": user_info[1],
            "firstname": user_info[2],
            "middlename": user_info[3] if user_info[3] else "",
            "course": user_info[4],
            "year_level": user_info[5],
            "email": user_info[6],
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
            "session": user_info[8],
            "points": user_info[9],
            "notification_count": notification_count
        }

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

    return render_template("history.html", pagetitle="Sit-in History", sit_in_records=sit_in_records, student_id=student_id, user=user_data)

@app.route("/reservation", methods=["GET", "POST"])
def reservation():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }

    if request.method == "POST":
        student_id = request.form["student_id"]
        full_name = request.form["full_name"]
        purpose = request.form["subject"]
        lab_number = request.form["room"]
        pc_number = request.form["pc"]
        date = request.form["date"]
        time_in = request.form["time_in"]

        # Check for schedule conflict
        if dbhelper.check_schedule_conflict(lab_number, date, time_in):
            flash("Reservation conflict: The selected lab is already scheduled for another session at this time.", "danger")
            return redirect(url_for("reservation"))

        # Insert reservation into the database
        success = dbhelper.insert_reservation(student_id, full_name, purpose, lab_number, pc_number, date, time_in)
        if success:
            flash("Reservation successful!", "success")
        else:
            flash("Failed to make a reservation. Please try again.", "danger")

        return redirect(url_for("reservation"))

    return render_template("reservation.html", pagetitle="Reservation", user=user_data)

@app.route("/view_feedback")
def view_feedback():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    feedbacks = dbhelper.get_feedbacks()
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template("feedback_report.html", pagetitle="Feedback Reports", feedbacks=feedbacks, pending_count=pending_count)
  

@app.route("/edit")
def edit():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }
    
    return render_template("edit.html", pagetitle="Edit Profile", user=user_data)

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
    total_reservations = dbhelper.get_total_reservations()
    announcements = dbhelper.get_announcements(include_inactive=True)
    purpose_counts = dbhelper.get_purpose_counts()
    leaderboard = dbhelper.get_leaderboard()
    pending_count = dbhelper.get_pending_reservation_count()

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
        total_reservations=total_reservations,
        leaderboard=leaderboard,
        pending_count=pending_count
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
    
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template("students.html", pagetitle="View Students", students=students, student=student, pending_count=pending_count)

@app.route("/view_sit_in")
def view_sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    search = request.args.get('search', '')
    sit_in_records = dbhelper.get_all_sit_in_records(search)
    purpose_counts = dbhelper.get_purpose_counts()
    lab_counts = dbhelper.get_lab_counts()
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template("view_sit_in.html", pagetitle="View Sit-in Records", sit_in_records=sit_in_records, purpose_counts=purpose_counts, lab_counts=lab_counts, pending_count=pending_count)

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
    pending_count = dbhelper.get_pending_reservation_count()

    return render_template('sit_in.html', sit_ins=sit_ins, page=page, total_pages=total_pages, pagetitle="Current Sit-in", pending_count=pending_count)

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
    pending_count = dbhelper.get_pending_reservation_count()

    return render_template("sit_in_reports.html", pagetitle="Generate Reports", sit_in_records=sit_in_records, pending_count=pending_count)

@app.route('/reset_session/<int:idno>', methods=['POST'])
def reset_session(idno):
    if "user" not in session:
        return jsonify({"success": False, "message": "You need to log in first!"})

    if dbhelper.reset_session(idno):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Failed to reset session."})

@app.route('/laboratory', methods=["GET", "POST"])
def laboratory():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    # Check if user is admin
    user_type = dbhelper.get_user_type(session["user"])
    if user_type != "admin":
        flash("You don't have permission to access this page!", "danger")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        reservation_id = request.form.get("reservation_id")
        action = request.form.get("action")
        
        if reservation_id and action:
            # Get reservation details first
            reservation = dbhelper.get_reservation_by_id(reservation_id)
            if not reservation:
                flash("Reservation not found!", "danger")
                return redirect(url_for("laboratory"))
            
            # Check if user has active sit-in
            if dbhelper.check_user_active_sit_in(reservation['student_id']):
                flash("Cannot approve/disapprove reservation. User has an active sit-in session.", "danger")
                return redirect(url_for("laboratory"))
            
            # Get admin ID
            admin_id = dbhelper.get_admin_id(session["user"])
            
            # Update reservation status
            if dbhelper.update_reservation_status(reservation_id, action):
                # Create notification for the student
                lab_info = f"Room {reservation['lab_number']}, PC {reservation['pc_number']}"
                if action == 'approved':
                    message = f"Your reservation for {lab_info} on {reservation['date']} at {reservation['time_in']} has been approved."
                    dbhelper.create_notification(reservation['student_id'], message, 'success')
                else:
                    message = f"Your reservation for {lab_info} on {reservation['date']} at {reservation['time_in']} has been disapproved."
                    dbhelper.create_notification(reservation['student_id'], message, 'danger')
                
                flash(f"Reservation {action} successfully!", "success")
            else:
                flash("Failed to update reservation status!", "danger")
    
    # Get all reservations
    reservations = dbhelper.get_reservations()
    selected_lab = request.args.get('lab', '524')  # Default to lab 524
    pending_count = dbhelper.get_pending_reservation_count()
    
    # Get logs data
    logs = dbhelper.get_logs()
    
    return render_template('laboratory.html', pagetitle="Laboratory Management", 
                          reservations=reservations, selectedLab=selected_lab, 
                          pending_count=pending_count, logs=logs)

# Add a new route to get user notifications
@app.route('/notifications')
def notifications():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for('login'))
    
    student_id = user_info[0]  # Get the student ID
    notifications = dbhelper.get_user_notifications(student_id)
    
    return render_template('notifications.html', pagetitle="Notifications", 
                          notifications=notifications, user=user_info)

# Add a route to mark notifications as read
@app.route('/mark_notification_read/<int:notification_id>')
def mark_notification_read(notification_id):
    if "user" not in session:
        return jsonify({"success": False})
    
    success = dbhelper.mark_notification_as_read(notification_id)
    return jsonify({"success": success})


@app.route('/get_pc_status/<lab_number>', methods=['GET'])
def get_pc_status(lab_number):
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"})
    
    pcs = dbhelper.get_lab_pc_availability(lab_number)
    return jsonify({"success": True, "pcs": pcs})

@app.route('/update_pc_status', methods=['POST'])
def update_pc_status():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    lab_number = data.get('lab_number')
    pc_numbers = data.get('pc_numbers')
    status = data.get('status')
    
    if not lab_number or not pc_numbers or not status:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    for pc_number in pc_numbers:
        if not dbhelper.update_pc_status(lab_number, pc_number, status):
            return jsonify({'success': False, 'message': 'Failed to update status'})
    
    return jsonify({'success': True, 'message': 'Status updated successfully'})

@app.route('/add_points_and_logout/<int:idno>', methods=['POST'])
def add_points_and_logout(idno):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    # Update points and set status to inactive
    dbhelper.add_points_and_logout(idno)
    flash("Points added and logged out!", "success")
    return redirect(url_for('sit_in'))

@app.route("/logs")
def logs():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    logs = dbhelper.get_logs()
    return render_template("logs.html", pagetitle="Logs", logs=logs)

@app.route("/resources", methods=["GET", "POST"])
def resources():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    # Create resources directory if it doesn't exist
    resources_dir = os.path.join(app.config["UPLOAD_FOLDER"], "resources")
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir)

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected!", "danger")
            return redirect(url_for("resources"))

        file = request.files["file"]
        title = request.form["title"]
        description = request.form["description"]

        if file.filename == "":
            flash("No file selected!", "danger")
            return redirect(url_for("resources"))

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(resources_dir, filename)  # Save to resources subfolder
            file.save(filepath)

            if dbhelper.insert_resource(title, description, filename):
                flash("Resource uploaded successfully!", "success")
            else:
                flash("Failed to upload resource.", "danger")

    resources = dbhelper.get_resources()
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template("resources.html", pagetitle="Resources", resources=resources, pending_count=pending_count)

@app.route("/edit_resource/<int:resource_id>", methods=["POST"])
def edit_resource(resource_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"]

    if dbhelper.update_resource(resource_id, title, description):
        flash("Resource updated successfully!", "success")
    else:
        flash("Failed to update resource.", "danger")

    return redirect(url_for("resources"))

@app.route("/download_resource/<int:resource_id>")
def download_resource(resource_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    resource = dbhelper.get_resource_by_id(resource_id)
    if not resource:
        flash("Resource not found!", "danger")
        return redirect(url_for("resources"))
    
    filename = resource[3]  # Assuming the filename is at index 3 in the resource tuple
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], "resources", filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        flash("File not found on server!", "danger")
        return redirect(url_for("resources"))
        
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route("/delete_resource/<int:resource_id>", methods=["POST"])
def delete_resource(resource_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if dbhelper.delete_resource(resource_id):
        flash("Resource deleted successfully!", "success")
    else:
        flash("Failed to delete resource.", "danger")

    return redirect(url_for("resources"))

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    # Get user info
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
    
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])

    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "notification_count": notification_count
    }

    if request.method == "POST":
        lab_number = request.form["lab_number"]
        date = request.form["date"]
        time_start = request.form["time_start"]
        time_end = request.form["time_end"]
        purpose = request.form["purpose"]

        if dbhelper.add_lab_schedule(lab_number, date, time_start, time_end, purpose):
            flash("Reservation request submitted successfully!", "success")
        else:
            flash("Failed to submit reservation request. Try again.", "danger")

    schedules = dbhelper.get_all_schedules()
    return render_template("schedule.html", pagetitle="Schedule", schedules=schedules, user=user_data)


@app.route("/admin_schedule", methods=["GET", "POST"])
def admin_schedule():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        schedule_id = request.form["schedule_id"]
        lab_number = request.form["lab_number"]
        date = request.form["date"]
        time_start = request.form["time_start"]
        time_end = request.form["time_end"]
        subject = request.form["subject"]
        instructor = request.form["instructor"]
        if not all([lab_number, date, time_start, time_end, subject, instructor]):
            flash("Please fill out all fields!", "danger")
            return redirect(url_for("admin_schedule"))
        if dbhelper.add_lab_schedule(lab_number, date, time_start, time_end, subject, instructor):
            flash("Schedule added successfully!", "success")
        else:
            flash("Failed to add schedule. Try again.", "danger")

    schedules = dbhelper.get_all_schedules()
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template("admin_schedule.html", pagetitle="Manage Schedule", schedules=schedules, pending_count=pending_count)

@app.route("/get_schedules_by_date", methods=["GET"])
def get_schedules_by_date():
    date = request.args.get('date')
    if not date:
        return jsonify({"success": False, "message": "Date parameter is required"})
    
    conn = dbhelper.connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, lab_number, time_start, time_end, subject, instructor, date FROM lab_schedule WHERE date = ? ORDER BY time_start", (date,))
    schedules = cursor.fetchall()
    conn.close()
    
    return jsonify({
        "success": True,
        "schedules": [{
            "id": row[0],
            "lab_number": row[1],
            "time_start": row[2],
            "time_end": row[3],
            "subject": row[4],
            "instructor": row[5],
            "date": row[6]
        } for row in schedules]
    })

@app.route("/add_lab_schedule", methods=["POST"])
def add_lab_schedule():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    lab_number = request.form.get("lab_number")
    date = request.form.get("date")
    time_start = request.form.get("time_start")
    time_end = request.form.get("time_end")
    subject = request.form.get("subject")
    instructor = request.form.get("instructor")

    if not all([lab_number, date, time_start, time_end, subject, instructor]):
        flash("Please fill out all fields!", "danger")
        return redirect(url_for("admin_schedule"))

    if dbhelper.add_lab_schedule(lab_number, date, time_start, time_end, subject, instructor):
        flash("Schedule added successfully!", "success")
    else:
        flash("Failed to add schedule. Try again.", "danger")

    return redirect(url_for("admin_schedule"))

@app.route("/update_lab_schedule", methods=["POST"])
def update_lab_schedule():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    schedule_id = request.form["schedule_id"]
    lab_number = request.form["lab_number"]
    date = request.form["date"]
    time_start = request.form["time_start"]
    time_end = request.form["time_end"]
    subject = request.form["subject"]
    instructor = request.form["instructor"]

    if dbhelper.update_lab_schedule(schedule_id, lab_number, date, time_start, time_end, subject, instructor):
        flash("Schedule updated successfully!", "success")
    else:
        flash("Failed to update schedule. Try again.", "danger")
    
    return redirect(url_for("admin_schedule"))

@app.route("/delete_lab_schedule", methods=["POST"])
def delete_lab_schedule():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    schedule_id = request.form.get("schedule_id")
    if not schedule_id:
        flash("Schedule ID is required!", "danger")
        return redirect(url_for("admin_schedule"))

    if dbhelper.delete_lab_schedule(schedule_id):
        flash("Schedule deleted successfully!", "success")
    else:
        flash("Failed to delete schedule. Try again.", "danger")

    return redirect(url_for("admin_schedule"))

@app.route("/download_schedules_pdf")
def download_schedules_pdf():
    pdf = FPDF(orientation='L')
    pdf.add_page()

    # Header 1: University of Cebu - Main Campus
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'University of Cebu - Main Campus', 0, 1, 'C')
    pdf.ln(2)

    # Header 2: Department of Computer Studies
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Department of Computer Studies', 0, 1, 'C')
    pdf.ln(2)

    # Header 3: Laboratory Schedules
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Laboratory Schedules', 0, 1, 'C')
    pdf.ln(8)

    # Table header colors
    pdf.set_fill_color(156, 39, 176)  # #9c27b0
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font('Arial', 'B', 12)
    col_width = pdf.w / 6
    pdf.cell(col_width, 10, 'Lab Number', 1, 0, 'C', 1)
    pdf.cell(col_width, 10, 'Date', 1, 0, 'C', 1)
    pdf.cell(col_width, 10, 'Time Start', 1, 0, 'C', 1)
    pdf.cell(col_width, 10, 'Time End', 1, 0, 'C', 1)
    pdf.cell(col_width, 10, 'Subject', 1, 0, 'C', 1)
    pdf.cell(col_width, 10, 'Instructor', 1, 1, 'C', 1)

    # Table rows
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(211, 186, 250)  # #D3BAFA
    schedules = dbhelper.get_all_schedules()
    for schedule in schedules:
        pdf.cell(col_width, 10, str(schedule['lab_number']), 1, 0, 'C', 1)
        pdf.cell(col_width, 10, str(schedule['date']), 1, 0, 'C', 1)
        pdf.cell(col_width, 10, str(schedule['time_start']), 1, 0, 'C', 1)
        pdf.cell(col_width, 10, str(schedule['time_end']), 1, 0, 'C', 1)
        pdf.cell(col_width, 10, str(schedule['subject']), 1, 0, 'C', 1)
        pdf.cell(col_width, 10, str(schedule['instructor']), 1, 1, 'C', 1)

    pdf_output = pdf.output(dest='S').encode('latin1')
    return send_file(
        io.BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='laboratory_schedules.pdf'
    )

@app.route("/student_resources")
def student_resources():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }
    
    resources = dbhelper.get_resources()
    return render_template("student_resources.html", pagetitle="Resources", resources=resources, user=user_data)

@app.route("/reservation_history")
def reservation_history():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
        
    user_info = dbhelper.get_user_info(session["user"])
    if not user_info:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))
        
    # Get notification count
    notification_count = dbhelper.get_unread_notification_count(user_info[0])
    
    # Create user data dictionary for template
    user_data = {
        "idno": user_info[0],
        "lastname": user_info[1],
        "firstname": user_info[2],
        "middlename": user_info[3] if user_info[3] else "",
        "course": user_info[4],
        "year_level": user_info[5],
        "email": user_info[6],
        "profile_image": user_info[7] if len(user_info) > 7 else "default.png",
        "session": user_info[8],
        "points": user_info[9],
        "notification_count": notification_count
    }
    
    reservations = dbhelper.get_reservation_history_by_username(session["user"])
    return render_template("reservation_history.html", pagetitle="Reservation History", reservations=reservations, user=user_data)

@app.route("/delete_schedule/<int:schedule_id>", methods=["POST"])
def delete_schedule(schedule_id):
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    if dbhelper.delete_lab_schedule(schedule_id):
        flash("Schedule deleted successfully!", "success")
    else:
        flash("Failed to delete schedule. Try again.", "danger")

    return redirect(url_for("admin_schedule"))

@app.route('/admin/notifications')
def admin_notifications():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    notifications = dbhelper.get_admin_notifications()
    pending_count = dbhelper.get_pending_reservation_count()
    return render_template('admin_notifications.html', notifications=notifications, pending_count=pending_count, pagetitle="Notifications")

@app.route("/check_schedule_conflict", methods=["GET"])
def check_schedule_conflict():
    if "user" not in session:
        return jsonify({"success": False, "message": "Not logged in"})
    
    lab_number = request.args.get('lab_number')
    date = request.args.get('date')
    time_in = request.args.get('time_in')
    
    if not all([lab_number, date, time_in]):
        return jsonify({"success": False, "message": "Missing parameters"})
    
    has_conflict = dbhelper.check_schedule_conflict(lab_number, date, time_in)
    return jsonify({"success": True, "has_conflict": has_conflict})

if __name__ == "__main__":
    app.run(debug=True)

