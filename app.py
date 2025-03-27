from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os
from datetime import datetime

app = Flask(__name__)

# ✅ Local MySQL Database Configuration
db_config = {
    "host": "localhost",
    "database": "lead_db",
    "username": "root",
    "password": "Kingston#1234",
}

# ✅ Create MySQL Connection String
DATABASE_URL = f"mysql+mysqlconnector://{db_config['username']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# ✅ Whitelist of valid table names
VALID_TABLES = {"answered_outbound_calls", "answered_inbound_calls", "missed_outbound_calls", "missed_inbound_calls"}

# ✅ Function to Parse Datetime Strings
def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
    except (ValueError, TypeError):
        print(f"⚠️ Invalid datetime format: {value}")
        return None

# ✅ Function to Insert Data into MySQL
def insert_into_db(table_name, data):
    if table_name not in VALID_TABLES:
        print(f"❌ Invalid table name: {table_name}")
        return

    try:
        with engine.begin() as connection:
            sql = text(f"""
            INSERT INTO {table_name} (
                callID, dispnumber, caller_id, start_time, answer_stamp, end_time,
                callType, call_duration, destination, status, resource_url, missedFrom, hangup_cause
            ) VALUES (
                :callID, :dispnumber, :caller_id, :start_time, :answer_stamp, :end_time,
                :callType, :call_duration, :destination, :status, :resource_url, :missedFrom, :hangup_cause
            )
            """)

            data["start_time"] = parse_datetime(data.get("start_time"))
            data["answer_stamp"] = parse_datetime(data.get("answer_stamp"))
            data["end_time"] = parse_datetime(data.get("end_time"))

            connection.execute(sql, data)
            print(f"✅ Data inserted into {table_name}")

    except Exception as e:
        print(f"❌ Database Error: {str(e)}")

# ✅ Webhook Endpoints
@app.route('/')
def home():
    return "MySQL Webhook Receiver is Running", 200

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
    app.run(host='0.0.0.0', port=10000, debug=True)
