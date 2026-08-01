import sqlite3
import os

DB_NAME = "skin_disease.db"

DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


def create_database():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        patient_name TEXT,

        gender TEXT,

        disease TEXT,

        confidence REAL,

        risk TEXT,

        prediction_time TEXT,

        date TEXT

    )
    """)

    conn.commit()

    # ---------------------------------------------------------
    # Backward compatibility: if this is an existing database
    # created before patient_name/gender existed, add the
    # columns instead of failing.
    # ---------------------------------------------------------

    cursor.execute("PRAGMA table_info(predictions)")

    existing_columns = {row[1] for row in cursor.fetchall()}

    if "patient_name" not in existing_columns:

        cursor.execute(
            "ALTER TABLE predictions ADD COLUMN patient_name TEXT"
        )

    if "gender" not in existing_columns:

        cursor.execute(
            "ALTER TABLE predictions ADD COLUMN gender TEXT"
        )

    conn.commit()

    conn.close()


def save_prediction(disease,
                    confidence,
                    risk,
                    prediction_time,
                    date,
                    patient_name="",
                    gender=""):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO predictions

    (patient_name,gender,disease,confidence,risk,prediction_time,date)

    VALUES(?,?,?,?,?,?,?)

    """,

    (

        patient_name,

        gender,

        disease,

        confidence,

        risk,

        prediction_time,

        date

    )

    )

    conn.commit()

    conn.close()


def get_predictions():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT id, patient_name, gender, disease, confidence, risk, prediction_time, date

    FROM predictions

    ORDER BY id DESC

    """)

    data = cursor.fetchall()

    conn.close()

    return data