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
        return render_template("dashboard.html", pagetitle="Dashboard" , user=user_data, announcements=announcements)

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
    
    return render_template("history.html", pagetitle="Sit-in History")

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
    return render_template("admin_dashboard.html", pagetitle="Admin Dashboard", total_students=total_students, announcements=announcements, total_feedback=total_feedback)

@app.route("/view_stundets")
def view_students():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))

    students = dbhelper.get_students()
    return render_template("students.html", pagetitle="View Students", students=students)

@app.route('/search', methods=['GET', 'POST'])
def search_student_page():
    student = None
    if request.method == 'POST':
        idno = request.form['idno']
        student = dbhelper.search_student_by_id(idno)
        if not student:
            flash('Student not found', 'danger')
    return render_template('search.html', student=student, pagetitle="Search Student")

if __name__ == "__main__":
    app.run(debug=True)