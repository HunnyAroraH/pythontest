from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json
import requests

app = Flask(__name__)
CORS(app)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Load property data from JSON file
with open('properties.json') as f:
    properties = json.load(f)

# Mock viewing schedule data
viewings = []


@app.route('/')
def index():
    return "Hello, this is the GET request test!"


@app.route('/test', methods=['POST'])
def test_post():
    data = request.json
    return jsonify({
        "message": "POST request received!",
        "data_received": data
    })


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        response = client.chat.completions.create(model="gpt-4",
                                                  messages=[{
                                                      "role": "user",
                                                      "content": prompt
                                                  }],
                                                  max_tokens=50)

        return jsonify(
            {"response": response.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search_properties', methods=['POST'])
def search_properties():
    try:
        data = request.json
        city = data.get('city', '').lower()
        property_type = data.get('type', '').lower()
        bedrooms = data.get('bedrooms', 0)

        # Filter properties based on search criteria
        filtered_properties = [
            prop for prop in properties
            if (not city or prop['city'].lower() == city) and
            (not property_type or prop['type'].lower() == property_type) and (
                not bedrooms or prop['bedrooms'] == bedrooms)
        ]

        return jsonify({"properties": filtered_properties})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/schedule_viewing', methods=['POST'])
def schedule_viewing():
    try:
        data = request.json
        property_id = data.get('property_id')
        user_name = data.get('user_name')
        user_email = data.get('user_email')
        viewing_time = data.get('viewing_time')

        if not property_id or not user_name or not user_email or not viewing_time:
            return jsonify({"error": "Missing required information"}), 400

        viewing = {
            "property_id": property_id,
            "user_name": user_name,
            "user_email": user_email,
            "viewing_time": viewing_time
        }

        viewings.append(viewing)

        return jsonify({
            "message": "Viewing scheduled successfully",
            "viewing": viewing
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/capture_lead', methods=['POST'])
def capture_lead():
    try:
        data = request.json
        user_name = data.get('user_name')
        user_email = data.get('user_email')
        phone_number = data.get('phone_number')
        message = data.get('message')

        if not user_name or not user_email or not phone_number or not message:
            return jsonify({"error": "Missing required information"}), 400

        lead = {
            "Name": user_name,
            "Email": user_email,
            "Phone": phone_number,
            "Property References": message
        }

        # Send data to Make.com
        make_url = "https://hook.us1.make.com/7v71i695pgsoeu5p3458y6255dyrh4r6"
        make_response = requests.post(make_url, json=lead)
        print("Make.com response status:", make_response.status_code)
        print("Make.com response body:", make_response.text)

        # Send data to Airtable
        airtable_url = "https://api.airtable.com/v0/appK1JMhzmZ4YkUGv/tblLMxqRVLEuxuxYG"
        headers = {
            "Authorization": f"Bearer {os.getenv('AIRTABLE_API_KEY')}",
            "Content-Type": "application/json"
        }
        airtable_response = requests.post(airtable_url,
                                          headers=headers,
                                          json={"fields": lead})
        print("Airtable response status:", airtable_response.status_code)
        print("Airtable response body:", airtable_response.text)

        return jsonify({
            "message": "Lead captured successfully",
            "make_response": make_response.text,
            "airtable_response": airtable_response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
