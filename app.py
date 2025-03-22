from flask import Flask, request, jsonify
import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

# ✅ Load environment variables securely
load_dotenv()

app = Flask(__name__)

# ✅ Azure SQL Database Configuration from Environment Variables
db_config = {
    "server": os.getenv("AZURE_SQL_SERVER"),
    "database": os.getenv("AZURE_SQL_DATABASE"),
    "username": os.getenv("AZURE_SQL_USER"),
    "password": os.getenv("AZURE_SQL_PASSWORD"),
    "driver": "{ODBC Driver 17 for SQL Server}"
}

# ✅ Whitelist of valid table names to prevent SQL injection
VALID_TABLES = {
    "answered_outbound_calls",
    "answered_inbound_calls",
    "missed_outbound_calls",
    "missed_inbound_calls"
}

# ✅ Create Database Connection Function
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
        print(f"❌ Database Connection Error: {str(e)}")
        return None  # Ensure None is returned if connection fails

# ✅ Function to Insert Data into Azure SQL
def insert_into_db(table_name, data):
    if table_name not in VALID_TABLES:
        print(f"❌ Invalid table name: {table_name}")
        return
    
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        def parse_datetime(value):
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
            except (ValueError, TypeError):
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

    except pyodbc.Error as e:
        print(f"❌ Database Error: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ✅ Webhook Endpoints
@app.route('/')
def home():
    return "Azure SQL Webhook Receiver is Running", 200

@app.route('/answered_outbound', methods=['POST'])
def answered_outbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    data["callType"] = "answered_outbound"
    print(f"📞 Answered Outbound Call Received: {data}")
    insert_into_db("answered_outbound_calls", data)
    return jsonify({"message": "Answered outbound call received"}), 200

@app.route('/answered_inbound', methods=['POST'])
def answered_inbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    data["callType"] = "answered_inbound"
    print(f"📞 Answered Inbound Call Received: {data}")
    insert_into_db("answered_inbound_calls", data)
    return jsonify({"message": "Answered inbound call received"}), 200

@app.route('/missed_outbound', methods=['POST'])
def missed_outbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    data["callType"] = "missed_outbound"
    print(f"📞 Missed Outbound Call Received: {data}")
    insert_into_db("missed_outbound_calls", data)
    return jsonify({"message": "Missed outbound call received"}), 200

@app.route('/missed_inbound', methods=['POST'])
def missed_inbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    data["callType"] = "missed_inbound"
    print(f"📞 Missed Inbound Call Received: {data}")
    insert_into_db("missed_inbound_calls", data)
    return jsonify({"message": "Missed inbound call received"}), 200

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
