from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import pymysql
from datetime import datetime

app = Flask(__name__)

# ✅ Database Configuration
db_config = {
    "host": "kei-mysql-server.mysql.database.azure.com",
    "database": "daily_transferred_leads",
    "username": "adminuser",  # 👈 include server name
    "password": "Kingston#1234",
}

DATABASE_URL = (
    f"mysql+pymysql://{db_config['username']}:{db_config['password']}"
    f"@{db_config['host']}/{db_config['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
)

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# ✅ Allowed Tables
VALID_TABLES = {
    "answered_outbound_calls",
    "answered_inbound_calls",
    "missed_outbound_calls",
    "missed_inbound_calls"
}

# ✅ Function to Parse Datetime Strings
def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
    except (ValueError, TypeError):
        print(f"⚠ Invalid datetime format: {value}")
        return None

# ✅ Function to Insert Data
def insert_into_db(table_name, data):
    if table_name not in VALID_TABLES:
        print(f"❌ Invalid table name: {table_name}")
        return False

    try:
        with engine.begin() as connection:
            # ✅ Build the expected data dictionary manually
            insert_data = {
                "callID": data.get("CallSessionId"),
                "dispnumber": data.get("DisplayNumber"),
                "caller_id": data.get("SourceNumber"),
                "start_time": parse_datetime(data.get("StartTime")),
                "answer_stamp": parse_datetime(data.get("AnswerTime")),
                "end_time": parse_datetime(data.get("EndTime")),
                "callType": data.get("Direction"),
                "call_duration": data.get("Duration"),
                "destination": data.get("DestinationNumber"),
                "status": data.get("Status"),
                "resource_url": data.get("RecordingUrl"),
                "missedFrom": data.get("CallerSource"),
                "hangup_cause": data.get("HangupCause") or "unknown"
            }

            sql = text(f"""
                INSERT INTO {table_name} (
                    callID, dispnumber, caller_id, start_time, answer_stamp, end_time,
                    callType, call_duration, destination, status, resource_url, missedFrom, hangup_cause
                ) VALUES (
                    :callID, :dispnumber, :caller_id, :start_time, :answer_stamp, :end_time,
                    :callType, :call_duration, :destination, :status, :resource_url, :missedFrom, :hangup_cause
                )
            """)

            connection.execute(sql, insert_data)
            print(f"✅ Data inserted into {table_name}")
            return True

    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        return False

# ✅ Webhook Route
@app.route('/<call_type>', methods=['POST'])
def handle_call_webhook(call_type):
    table_mapping = {
        "answered_outbound": "answered_outbound_calls",
        "answered_inbound": "answered_inbound_calls",
        "missed_outbound": "missed_outbound_calls",
        "missed_inbound": "missed_inbound_calls"
    }

    table_name = table_mapping.get(call_type)
    if not table_name:
        return jsonify({"error": "Invalid call type"}), 400

    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No data received"}), 400

    success = insert_into_db(table_name, data)
    if success:
        return jsonify({"message": f"{call_type.replace('_', ' ').capitalize()} call received"}), 200
    else:
        return jsonify({"error": "Failed to insert data"}), 500

# ✅ Run Flask App (Fixed Port)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3306, debug=True)
