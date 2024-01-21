from flask import Flask, jsonify, render_template
from flask_cors import CORS
import csv
import googlemaps
from dotenv import load_dotenv
import os
from collections import defaultdict
import pandas as pd
from fpdf import FPDF

app = Flask(__name__)
CORS(app)

load_dotenv()
google_key = os.getenv("GOOGLE_SEARCH_ENGINE_KEY")
map_client = googlemaps.Client(key=google_key)

def geo_coding():

    global locations
    locations = defaultdict(lambda: {'nace_codes': []})

    with open('output.csv', 'r', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)  # Read the header row

        company_nr_index = 1
        company_name_index = 3
        address_index = 4
        nace_code_index = 6
        employee_nr_index = 7
        revenue_index = 8

        for row in csvreader:
            address = row[address_index]
            company_name = row[company_name_index] if company_name_index < len(row) else ''
            nace_code = row[nace_code_index]
            company_nr = row[company_nr_index]
            employee_nr = row[employee_nr_index]
            revenue = row[revenue_index]

            # Check if the address is not a placeholder and is not already processed
            if address != '-' and address != '' and company_name != "Geen gegevens opgenomen in KBO." and company_name != "-":

                response = map_client.geocode(address)
                if response:
                    location = response[0]['geometry']['location']
                    latitude = location['lat']
                    longitude = location['lng']

                    # Use defaultdict to store multiple NACE codes for each company
                    locations[address]['latitude'] = latitude
                    locations[address]['longitude'] = longitude
                    locations[address]['company_name'] = company_name
                    locations[address]['company_nr'] = company_nr
                    locations[address]['employee_nr'] = employee_nr
                    locations[address]['revenue'] = revenue
                    locations[address]['nace_codes'].append(nace_code)

        
        geojson = get_locations()
        return geojson

def get_locations():
    # Convert locations to a GeoJSON-like structure
    features = []
    company_names = []
    for address, data in locations.items():
        feature = {
            "type": "Feature",
            "properties": {
                "address": address,
                "company_name": data['company_name'],
                "company_nr": data['company_nr'],
                "employee_nr": data['employee_nr'],
                "revenue": data['revenue'],
                "nace_codes": data['nace_codes']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [data['longitude'], data['latitude']]
            }
        }
        features.append(feature)

        company_names.append(data['company_name'])

    # Save company names to a text file
    with open('C:/Users/Kristof Pipeleers/Desktop/SOCS project/Code/parameter_generator/companies.txt', 'w') as file:
        for company_name in company_names:
            file.write(company_name + '\n')

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
