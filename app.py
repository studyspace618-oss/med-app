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
            
        last_date = data.get("last_date", str(datetime.now().date()))
        today = str(datetime.now().date())
        meds = data.get("medicines", [])
        
        if last_date != today:
            # NEW DAY RESET
            for med in meds:
                for slot in med["slots"]:
                    med["slots"][slot]["taken"] = False
            
            # Save the reset state immediately
            save_data(meds)
            return meds
            
        return meds
    return []

def save_data(med_list):
    payload = {
        "last_date": str(datetime.now().date()),
        "medicines": med_list
    }
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f, indent=4)

@app.route('/medicines', methods=['GET'])
def get_medicines():
    current_meds = load_data() # This triggers the date check
    return jsonify(current_meds), 200

@app.route('/medicines', methods=['POST'])
def add_medicine():
    medicines = load_data()
    data = request.get_json(silent=True)
    slots_data = data.get('slots', {})
    
    new_med = {
        "id": int(datetime.now().timestamp()), # Unique ID based on time
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
    medicines = load_data()
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
    medicines = load_data()
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
    medicines = load_data()
    updated_meds = [m for m in medicines if m['id'] != med_id]
    save_data(updated_meds)
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    app.run(debug=False)
