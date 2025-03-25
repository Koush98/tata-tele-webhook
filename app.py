from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os
from datetime import datetime

app = Flask(__name__)

# ✅ Hardcoded Azure SQL Database Configuration (For Testing Only)
db_config = {
    "server": "kei-sql-server.database.windows.net",
    "database": "LeadManagementDB",
    "username": "adminuser",
    "password": "Kingston#1234",
}

# ✅ Create Database Connection Using SQLAlchemy with Safe ODBC Driver
DATABASE_URL = f"mssql+pyodbc://{db_config['username']}:{db_config['password']}@{db_config['server']}/{db_config['database']}?driver={{{'ODBC Driver 18 for SQL Server'}}}&TrustServerCertificate=yes"

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
# ✅ Whitelist of valid table names to prevent SQL injection
VALID_TABLES = {"answered_outbound_calls", "answered_inbound_calls", "missed_outbound_calls", "missed_inbound_calls"}

# ✅ Function to Parse Datetime Strings
def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
    except (ValueError, TypeError):
        print(f"⚠️ Invalid datetime format: {value}")
        return None

# ✅ Function to Insert Data into Azure SQL
def insert_into_db(table_name, data):
    if table_name not in VALID_TABLES:
        print(f"❌ Invalid table name: {table_name}")
        return

    try:
        with engine.begin() as connection:
            sql = text("""
            INSERT INTO {} (
                callID, dispnumber, caller_id, start_time, answer_stamp, end_time,
                callType, call_duration, destination, status, resource_url, missedFrom, hangup_cause
            ) VALUES (:callID, :dispnumber, :caller_id, :start_time, :answer_stamp, :end_time,
                      :callType, :call_duration, :destination, :status, :resource_url, :missedFrom, :hangup_cause)
            """.format(table_name))  

            data["start_time"] = parse_datetime(data.get("start_time"))
            data["answer_stamp"] = parse_datetime(data.get("answer_stamp"))
            data["end_time"] = parse_datetime(data.get("end_time"))

            connection.execute(sql, data)  # ✅ Secure SQL execution
            print(f"✅ Data inserted into {table_name}")

    except Exception as e:
        print(f"❌ Database Error: {str(e)}")

# ✅ Webhook Endpoints
@app.route('/')
def home():
    return "Azure SQL Webhook Receiver is Running", 200

@app.route('/answered_outbound', methods=['POST'])
def answered_outbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    insert_into_db("answered_outbound_calls", data)
    return jsonify({"message": "Answered outbound call received"}), 200

@app.route('/answered_inbound', methods=['POST'])
def answered_inbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    insert_into_db("answered_inbound_calls", data)
    return jsonify({"message": "Answered inbound call received"}), 200

@app.route('/missed_outbound', methods=['POST'])
def missed_outbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    insert_into_db("missed_outbound_calls", data)
    return jsonify({"message": "Missed outbound call received"}), 200

@app.route('/missed_inbound', methods=['POST'])
def missed_inbound():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400
    insert_into_db("missed_inbound_calls", data)
    return jsonify({"message": "Missed inbound call received"}), 200

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)
