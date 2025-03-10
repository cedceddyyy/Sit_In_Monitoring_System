import sqlite3

DB_NAME = "users.db"

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
                      password TEXT NOT NULL 
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
                      FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
                 )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                      feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      student_id INTEGER NOT NULL,
                      lab_number INTEGER NOT NULL,
                      date_submitted text default current_date,
                      message TEXT NOT NULL,    
                      FOREIGN KEY (student_id) REFERENCES users(idno) ON DELETE CASCADE
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

    cursor.execute("SELECT idno, lastname, firstname, middlename, course, year_level, email, username FROM users")
    users = cursor.fetchall()
    conn.close()

    return [{"idno": row[0], "lastname": row[1], "firstname": row[2], "middlename": row[3], "course": row[4], "year_level": row[5], "email": row[6]} for row in users]

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

def get_announcements():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT announcement_detail, date_created FROM announcement ORDER BY date_created DESC")
    announcements = cursor.fetchall()
    conn.close()

    return [{"announcement_detail": row[0], "date_created": row[1]} for row in announcements]

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


if __name__ == "__main__":
    create_database()
    print("Database Initialize Successful!")

