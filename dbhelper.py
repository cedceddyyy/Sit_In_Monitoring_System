import sqlite3
from datetime import datetime
import pytz

DB_NAME = "users.db"
TIMEZONE = "Asia/Manila"

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      idno INTEGER UNIQUE NOT NULL,
                      lastname VARCHAR(50) NOT NULL,
                      firstname VARCHAR(50) NOT NULL,
                      middlename VARCHAR(50) NULL,
                      course VARCHAR(10) NOT NULL,
                      year_level TINYINT NOT NULL,
                      email VARCHAR(50) NOT NULL,
                      username INTEGER NOT NULL,
                      password TEXT NOT NULL,
                      session INTEGER DEFAULT 30
                 )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS admin (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      lastname VARCHAR(50) NOT NULL,
                      firstname VARCHAR(50) NOT NULL,
                      middlename VARCHAR(50) NULL,
                      username VARCHAR(50) UNIQUE NOT NULL,
                      password TEXT NOT NULL 
                 )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS announcement (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      announcement_detail TEXT NOT NULL,
                      date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                      admin_id INTEGER NOT NULL,
                      status TEXT DEFAULT 'active',
                      FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
                 )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                      feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      student_id INTEGER NOT NULL,
                      lab_number INTEGER NOT NULL,
                      date_submitted DATETIME DEFAULT CURRENT_TIMESTAMP,
                      message TEXT NOT NULL,    
                      FOREIGN KEY (student_id) REFERENCES users(idno) ON DELETE CASCADE
                 )''')
    

    conn.execute('''CREATE TABLE IF NOT EXISTS sit_in (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      idno INTEGER NOT NULL,
                      purpose TEXT NOT NULL,
                      lab TEXT NOT NULL,
                      remaining_session INTEGER NOT NULL,
                      login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                      logout_time DATETIME NULL,
                      status TEXT DEFAULT 'active',
                      FOREIGN KEY (idno) REFERENCES users(idno) ON DELETE CASCADE,
                      FOREIGN KEY (remaining_session) REFERENCES users(session)
                 )''')

    conn.commit()
    conn.close()

def register_user(idno, lastname, firstname, middlename, course, year_level, email, username, password):
    conn = connect_db()
    cursor = conn.cursor()

    try: 
        cursor.execute("INSERT INTO users (idno, lastname, firstname, middlename, course, year_level, email, username, password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)" , (idno, lastname, firstname, middlename, course, year_level, email, username, password))
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validate_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    admin = cursor.fetchone()

    conn.close()

    if admin:
        return "admin"  # Return 'admin' if the user is in the admin table
    elif user:
        return "user"  # Return 'user' if found in users table
    else:
        return None  # Invalid credentials

def get_user_info(username):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT idno, lastname, firstname, middlename, course, year_level, email, profile_image FROM users WHERE username = ? ", (username,))
    user_info = cursor.fetchone()
    conn.close()

    return user_info

def get_students():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT idno, lastname, firstname, middlename, course, year_level, email, session FROM users")
    users = cursor.fetchall()
    conn.close()

    return [{"idno": row[0], "lastname": row[1], "firstname": row[2], "middlename": row[3], "course": row[4], "year_level": row[5], "email": row[6], "session": row[7]} for row in users]

def update_user_info(username, lastname, firstname, middlename, course, year_level, email):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''UPDATE users 
                      SET lastname = ?, firstname = ?, middlename = ?, course = ?, year_level = ?, email = ? 
                      WHERE username = ?''',
                   (lastname, firstname, middlename, course, year_level, email, username))
    
    conn.commit()
    conn.close()

def update_profile_picture(username, filename):
    conn = connect_db()
    cursor = conn.cursor()

    # Update the profile_image field for the specified user
    cursor.execute("UPDATE users SET profile_image = ? WHERE username = ?", (filename, username))
    conn.commit()
    conn.close()

def insert_announcement(announcement_detail, admin_id):
    conn = connect_db()
    cursor = conn.cursor()

    try: 
        cursor.execute("INSERT INTO announcement (announcement_detail, admin_id) VALUES (?, ?)" , (announcement_detail, admin_id))
        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_admin_id(username):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM admin WHERE username = ?", (username,))
    admin_id = cursor.fetchone()
    conn.close()

    return admin_id[0] if admin_id else None

def format_datetime(dt_str):
    local_tz = pytz.timezone(TIMEZONE)
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    dt = dt.astimezone(local_tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_announcements(include_inactive=False):
    conn = connect_db()
    cursor = conn.cursor()
    
    if include_inactive:
        cursor.execute("SELECT id, announcement_detail, date_created, status FROM announcement ORDER BY date_created desc")
    else:
        cursor.execute("SELECT id, announcement_detail, date_created FROM announcement WHERE status = 'active' ORDER BY date_created desc")
    
    announcements = cursor.fetchall()
    conn.close()
    return [(row[0], row[1], format_datetime(row[2]), row[3] if include_inactive else None) for row in announcements]

def total_students():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()

    return total

def total_feedback():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM feedback")
    total = cursor.fetchone()[0]
    conn.close()

    return total

def insert_feedback(student_id, lab_number, message):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO feedback (student_id, lab_number, message) VALUES (?, ?, ?)", 
                       (student_id, lab_number, message))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_feedbacks():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, lab_number, message, date_submitted FROM feedback ORDER BY date_submitted DESC")
    feedback_details = cursor.fetchall()
    conn.close()

    # Convert tuples to dictionaries
    return [{"student_id": row[0], "lab_number": row[1], "message": row[2], "date_submitted": row[3]} for row in feedback_details]

def search_student_by_id(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT idno, lastname, firstname, middlename FROM users WHERE idno = ?", (idno,))
    student = cursor.fetchone()
    conn.close()

    return student

def insert_sit_in(idno, purpose, lab, login_time):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO sit_in (idno, purpose, lab, remaining_session, login_time) VALUES (?, ?, ?, (SELECT session FROM users WHERE idno = ?), ?)", 
                       (idno, purpose, lab, idno, login_time))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def update_logout_time(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE sit_in SET logout_time = CURRENT_TIMESTAMP, status = 'inactive' WHERE idno = ? AND logout_time IS NULL", (idno,))
    conn.commit()
    conn.close()

def decrement_session(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET session = session - 1 WHERE idno = ?", (idno,))
    cursor.execute("UPDATE sit_in SET remaining_session = (SELECT session FROM users WHERE idno = ?) WHERE idno = ? AND status = 'active'", (idno, idno))
    conn.commit()
    conn.close()

def update_login_time(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE sit_in SET login_time = CURRENT_TIMESTAMP WHERE idno = ? AND logout_time IS NULL", (idno,))
    conn.commit()
    conn.close()

def update_status_to_active(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE sit_in SET status = 'active' WHERE idno = ? AND status != 'active'", (idno,))
    conn.commit()
    conn.close()

def get_sit_ins(search, page, per_page):
    conn = connect_db()
    cursor = conn.cursor()

    offset = (page - 1) * per_page
    search_query = f"%{search}%"

    cursor.execute('''SELECT sit_in.idno, users.lastname || ' ' || users.firstname || ' ' || IFNULL(users.middlename, '') AS full_name, sit_in.purpose, sit_in.lab, sit_in.remaining_session, sit_in.login_time
                      FROM sit_in
                      JOIN users ON  sit_in.idno = users.idno
                      WHERE (sit_in.idno LIKE ? OR sit_in.purpose LIKE ?) AND sit_in.status = 'active'
                      ORDER BY sit_in.login_time DESC
                      LIMIT ? OFFSET ?''', (search_query, search_query, per_page, offset))
    sit_ins = cursor.fetchall()

    cursor.execute('''SELECT COUNT(*)
                      FROM sit_in
                      WHERE (idno LIKE ? OR purpose LIKE ?) AND status = 'active' ''', (search_query, search_query))
    total_records = cursor.fetchone()[0]
    total_pages = (total_records + per_page - 1) // per_page

    conn.close()

    return [{"idno": row[0], "full_name": row[1], "purpose": row[2], "lab": row[3], "remaining_session": row[4], "login_time": row[5]} for row in sit_ins], total_pages

def get_sit_in_history(idno):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''SELECT date(login_time) as date, login_time, logout_time, lab 
                      FROM sit_in 
                      WHERE idno = ? 
                      ORDER BY login_time DESC''', (idno,))
    history = cursor.fetchall()
    conn.close()

    return [{"date": row[0], "login_time": row[1], "logout_time": row[2], "lab": row[3]} for row in history]

def get_all_sit_in_records(search=''):
    conn = connect_db()
    cursor = conn.cursor()

    search_query = f"%{search}%"
    cursor.execute('''SELECT sit_in.idno, users.lastname || ' ' || users.firstname || ' ' || IFNULL(users.middlename, '') AS full_name, 
                      sit_in.purpose, sit_in.lab, sit_in.login_time, sit_in.logout_time, date(sit_in.login_time) as date
                      FROM sit_in
                      JOIN users ON sit_in.idno = users.idno
                      WHERE sit_in.idno LIKE ? OR sit_in.purpose LIKE ? OR users.lastname LIKE ? OR users.firstname LIKE ?
                      ORDER BY sit_in.login_time DESC''', (search_query, search_query, search_query, search_query))
    records = cursor.fetchall()
    conn.close()

    return [{"idno": row[0], "full_name": row[1], "purpose": row[2], "lab": row[3], "login_time": format_datetime(row[4]), "logout_time": format_datetime(row[5]) if row[5] else None, "date": row[6]} for row in records]

def reset_all_sessions():
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET session = 30")
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_purpose_counts():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT purpose, COUNT(*) FROM sit_in GROUP BY purpose")
    purpose_counts = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in purpose_counts}

def get_lab_counts():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT lab, COUNT(*) FROM sit_in GROUP BY lab")
    lab_counts = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in lab_counts}

def total_sit_in():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM sit_in")
    total = cursor.fetchone()[0]
    conn.close()

    return total

def update_announcement_status(announcement_id, status):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE announcement SET status = ? WHERE id = ?", (status, announcement_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def delete_announcement(announcement_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM announcement WHERE id = ?", (announcement_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    print("Database Initialize Successful!")

