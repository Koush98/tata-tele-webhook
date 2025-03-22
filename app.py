from flask import Flask, request, jsonify
import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ Azure SQL Database Configuration
db_config = {
    "server": os.getenv("AZURE_SQL_SERVER"),
    "database": os.getenv("AZURE_SQL_DATABASE"),
    "username": os.getenv("AZURE_SQL_USER"),
    "password": os.getenv("AZURE_SQL_PASSWORD"),
    "driver": "{ODBC Driver 17 for SQL Server}"
}

# ✅ Allowed table names
VALID_TABLES = {
    "answered_outbound_calls",
    "answered_inbound_calls",
    "missed_outbound_calls",
    "missed_inbound_calls"
}

# ✅ Get database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={db_config['driver']};"
            f"SERVER={db_config['server']};"
            f"DATABASE={db_config['database']};"
            f"UID={db_config['username']};"
            f"PWD={db_config['password']}"
        )
        return conn
    except pyodbc.Error as e:
        print(f"❌ Database Connection Error: {e}")
        return None

# ✅ Insert data function
def insert_into_db(table_name, data):
    if table_name not in VALID_TABLES:
        print(f"❌ Invalid table name: {table_name}")
        return False

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # ✅ Helper function for datetime parsing
        def parse_datetime(value):
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
            except ValueError:
                print(f"⚠️ Invalid datetime format: {value}")
                return None

        sql = f"""
        INSERT INTO {table_name} (
            callID, dispnumber, caller_id, start_time, answer_stamp, end_time,
            callType, call_duration, destination, status, resource_url, missedFrom, hangup_cause
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            data.get("callID"), data.get("dispnumber"), data.get("caller_id"),
            parse_datetime(data.get("start_time")), parse_datetime(data.get("answer_stamp")),
            parse_datetime(data.get("end_time")), data.get("callType"),
            data.get("call_duration"), data.get("destination"), data.get("status"),
            data.get("resource_url"), data.get("missedFrom"), data.get("hangup_cause")
        )

        cursor.execute(sql, values)
        conn.commit()
        print(f"✅ Data inserted into {table_name}")

        return True

    except pyodbc.Error as e:
        print(f"❌ Database Error: {e}")
        return False

    finally:
        cursor.close()
        conn.close()

# ✅ Webhook Routes
@app.route('/')
def home():
    return "Azure SQL Webhook Receiver is Running", 200

@app.route('/<call_type>', methods=['POST'])
def handle_calls(call_type):
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    table_mapping = {
        "answered_outbound": "answered_outbound_calls",
        "answered_inbound": "answered_inbound_calls",
        "missed_outbound": "missed_outbound_calls",
        "missed_inbound": "missed_inbound_calls"
    }

    table_name = table_mapping.get(call_type)
    if not table_name:
        return jsonify({"error": "Invalid call type"}), 400

    data["callType"] = call_type
    print(f"📞 {call_type.replace('_', ' ').title()} Call Received: {data}")

    if insert_into_db(table_name, data):
        return jsonify({"message": f"{call_type.replace('_', ' ').title()} call received"}), 200
    else:
        return jsonify({"error": "Database insertion failed"}), 500

# ✅ Run Flask App
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
