import sqlite3

def init_db():
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    # Create the chatters table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            messages INTEGER NOT NULL
        )
    ''')
    
    # Insert dummy data only if table is empty
    cursor.execute("SELECT COUNT(*) FROM chatters")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('Alice', 120),
            ('Bob', 95),
            ('Charlie', 75),
            ('David', 60),
            ('Eva', 45)
        ]
        cursor.executemany("INSERT INTO chatters (name, messages) VALUES (?, ?)", sample_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

