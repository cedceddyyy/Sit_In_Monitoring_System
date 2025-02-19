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
    conn.close()

    return user is not None

def get_user_info(username):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT idno, lastname, firstname, middlename, course, year_level, email, profile_image FROM users WHERE username = ? ", (username,))
    user_info = cursor.fetchone()
    conn.close()

    return user_info

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


if __name__ == "__main__":
    create_database()
    print("Database Initialize Successful!")

