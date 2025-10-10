from flask import Flask, jsonify, request
from entity_attributes import get_entities_by_type, extract_all_entity_info_to_dict

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "message": "FIWARE → Grafana adapter is running. Use /data?type=<EntityType>"
    })

@app.route("/data")
def get_data():
    entity_type = request.args.get("type")
    if not entity_type:
        return jsonify({"error": "Missing 'type' parameter"}), 400

    # Fetch and transform data from Orion Context Broker
    entities_raw_data = get_entities_by_type(entity_type)
    if not entities_raw_data:
        return jsonify({"error": f"No entities found for type '{entity_type}'"}), 404

    transformed_data = [
        extract_all_entity_info_to_dict(entity)
        for entity in entities_raw_data
    ]

    return jsonify(transformed_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)