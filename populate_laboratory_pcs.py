import sqlite3

DB_NAME = "users.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def populate_laboratory_pcs():
    conn = connect_db()
    cursor = conn.cursor()

    # List of laboratory numbers
    lab_numbers = ['524', '526', '528', '530', '542', '544']

    try:
        for lab_number in lab_numbers:
            for pc_number in range(1, 51):  # 50 PCs per lab
                cursor.execute('''
                    INSERT INTO laboratory_pcs (lab_number, pc_number, status)
                    VALUES (?, ?, 'available')
                ''', (lab_number, pc_number))
        
        conn.commit()
        print("Laboratory PCs populated successfully!")
    except sqlite3.Error as e:
        print(f"Error populating laboratory PCs: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_laboratory_pcs()