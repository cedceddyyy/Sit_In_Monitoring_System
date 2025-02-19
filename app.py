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
        if "register" in request.form:  
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


        else:  
            username = request.form["username"]
            password = request.form["password"]

            if dbhelper.validate_user(username, password):
                session["user"] = username
                flash("Login Successful!", "success")
                return redirect("/")  
            else:
                flash("Invalid credentials! Try again.", "danger")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("You need to log in first!", "danger")
        return redirect(url_for("login"))
    return render_template("dashboard.html", pagetitle="Dashboard", user=session["user"])

@app.route("/info")
def info():
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
        return render_template("info.html", pagetitle="Information" , user=user_data)
    
    flash("User not found!", "danger")
    return redirect(url_for('dashboard'))

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
        return redirect(url_for("info"))

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

if __name__ == "__main__":
    app.run(debug=True)