import sqlite3

conn = sqlite3.connect(
    "sms_gateway.db",
    check_same_thread=False
)

cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS sms_logs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    message_id TEXT,

    source_addr TEXT,

    destination_addr TEXT,

    message TEXT,

    status TEXT
)
""")


conn.commit()


def save_sms(sms):

    cursor.execute("""
    INSERT INTO sms_logs (

        message_id,
        source_addr,
        destination_addr,
        message,
        status

    ) VALUES (?, ?, ?, ?, ?)
    """, (

        sms["message_id"],
        sms["source_addr"],
        sms["destination_addr"],
        sms["message"],
        sms["status"]
    ))

    conn.commit()

    print("\n💾 SMS saved to database")

