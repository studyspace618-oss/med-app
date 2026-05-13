import json
import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = "medicines.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Daily Reset Logic: Check if the last save was yesterday
            last_date = data.get("last_date", str(datetime.now().date()))
            today = str(datetime.now().date())
            
            if last_date != today:
                # New day! Reset all 'taken' flags to False
                for med in data.get("medicines", []):
                    for slot in med["slots"]:
                        med["slots"][slot]["taken"] = False
                data["last_date"] = today
                save_data(data.get("medicines", []))
            return data.get("medicines", [])
    return []

def save_data(med_list):
    payload = {
        "last_date": str(datetime.now().date()),
        "medicines": med_list
    }
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f, indent=4)

medicines = load_data()

@app.route('/medicines', methods=['GET'])
def get_medicines():
    global medicines
    medicines = load_data() # Refresh data and check for reset
    return jsonify(medicines), 200

@app.route('/medicines', methods=['POST'])
def add_medicine():
    data = request.get_json(silent=True)
    slots_data = data.get('slots', {})
    new_med = {
        "id": len(medicines) + 1,
        "name": str(data.get('name')),
        "dosage": str(data.get('dosage', 'N/A')),
        "stock": int(data.get('stock', 0)),
        "food": str(data.get('food', 'Before Food')),
        "slots": {
            "morning": {"required": slots_data.get('morning', False), "taken": False},
            "noon": {"required": slots_data.get('noon', False), "taken": False},
            "evening": {"required": slots_data.get('evening', False), "taken": False}
        }
    }
    medicines.append(new_med)
    save_data(medicines)
    return jsonify(new_med), 201

@app.route('/medicines/<int:med_id>/take/<slot>', methods=['POST'])
def take_medicine(med_id, slot):
    for med in medicines:
        if med['id'] == med_id:
            if med['stock'] > 0:
                med['slots'][slot]['taken'] = True
                med['stock'] -= 1
                save_data(medicines)
                return jsonify({"success": True}), 200
    return jsonify({"error": "Failed"}), 400

@app.route('/medicines/<int:med_id>/refill', methods=['POST'])
def refill_medicine(med_id):
    data = request.get_json()
    amount = int(data.get('amount', 0))
    for med in medicines:
        if med['id'] == med_id:
            med['stock'] += amount
            save_data(medicines)
            return jsonify({"success": True}), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/medicines/<int:med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    global medicines
    medicines = [m for m in medicines if m['id'] != med_id]
    save_data(medicines)
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)