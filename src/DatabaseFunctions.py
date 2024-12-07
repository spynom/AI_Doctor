import sqlite3

def get_db_connection():
    conn = sqlite3.connect("chat_history.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_application_logs():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_query TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()



def insert_application_logs(session_id, user_query, response):
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, response) VALUES (?, ?, ?)',
                 (session_id, user_query, response))
    conn.commit()
    conn.close()


@staticmethod
def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, response FROM application_logs WHERE session_id = ? ORDER BY created_at',
                   (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['response']}
        ])
    conn.close()
    return messages


def get_sessions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT session_id FROM application_logs')
    sessions = []
    for row in cursor.fetchall():
        sessions.append(row['session_id'])

    conn.close()
    return sessions