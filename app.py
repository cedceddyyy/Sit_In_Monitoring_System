from flask import Flask, render_template, request, redirect, session, flash, url_for
import dbhelper
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "Cedric@#123"

app.config["UPLOAD_FOLDER"] = "static/uploads"
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
                    dbhelper.update_login_time(user_info[0])  # Update login time using idno
                flash("Login Successful!", "success")
                return redirect(url_for("dashboard"))  # Redirect regular user

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
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png"
        }
        return render_template("dashboard.html", pagetitle="Dashboard", user=user_data, announcements=announcements)

    flash("User not found!", "danger")
    return redirect(url_for('dashboard'))

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
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png"
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
    if dbhelper.insert_announcement(announcement_detail, admin_id):
        flash("Announcement posted successfully!", "success")
    else:
        flash("Failed to post announcement. Try again.", "danger")

    return redirect(url_for("admin_dashboard"))

@app.route("/rules")
def rules():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    return render_template("rules.html", pagetitle="Rules")

@app.route("/history")
def history():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    
    # Query the sit_in table to get the records
    user_info = dbhelper.get_user_info(session["user"])
    if user_info:
        sit_in_records = dbhelper.get_sit_in_history(user_info[0])
    else:
        sit_in_records = []
    
    return render_template("history.html", pagetitle="Sit-in History", sit_in_records=sit_in_records)

@app.route("/reservation")
def reservation():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    return render_template("reservation.html", pagetitle="Reservation")

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    # Fetch student ID from the session
    user_id = dbhelper.get_user_info(session["user"])
    if user_id:
        student_id = user_id[0]  
    else:
        flash("User not found!", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        lab_number = request.form.get('lab_number')
        message = request.form.get('message')

        if not lab_number or not message:
            flash("Please fill out all fields!", "danger")      
        else:
            success = dbhelper.insert_feedback(student_id, lab_number, message)
            if success:
                flash("Feedback submitted successfully!", "success")    
            else:
                flash("Failed to submit feedback. Try again.", "danger")

    return render_template("feedback.html", pagetitle="Feedback", student_id=student_id)

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
            "profile_image": user_info[7] if len(user_info) > 7 else "default.png"    
        }
        return render_template("edit.html", pagetitle="Edit Information", user=user_data)

    flash("User not found!", "danger")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    if "user" in session:
        user_info = dbhelper.get_user_info(session["user"])
        if user_info:
            dbhelper.update_logout_time(user_info[0])  # Update logout time and status using idno
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
    announcements = dbhelper.get_announcements()
    purpose_counts = dbhelper.get_purpose_counts()
    return render_template("admin_dashboard.html", pagetitle="Admin Dashboard", total_students=total_students, announcements=announcements, total_feedback=total_feedback, purpose_counts=purpose_counts)

@app.route("/view_students")
def view_students():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    students = dbhelper.get_students()
    return render_template("students.html", pagetitle="View Students", students=students)

@app.route("/view_sit_in")
def view_sit_in():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    sit_in_records = dbhelper.get_all_sit_in_records()
    return render_template("view_sit_in.html", pagetitle="View Sit-in Records", sit_in_records=sit_in_records)

@app.route('/search', methods=['GET', 'POST'])
def search_student_page():
    student = None
    if request.method == 'POST':
        idno = request.form['idno']
        student = dbhelper.search_student_by_id(idno)
        if not student:
            flash('Student not found', 'danger')
    return render_template('search.html', student=student, pagetitle="Search Student")

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
        dbhelper.update_status_to_active(idno)  # Update status to active
        flash("Sit-In recorded successfully!", "success")
    else:
        flash("Failed to record Sit-In. Try again.", "danger")

    return redirect(url_for('search_student_page'))

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

if __name__ == "__main__":
    app.run(debug=True)