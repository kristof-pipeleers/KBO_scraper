import gradio as gr
from KBO_scraper import kbo_scraper
from geo_coding import geo_coding
import pandas as pd
import folium
import folium.plugins as plugins
import json


def run_scraper(nace_codes, location_option, location):
    nace_codes_list = nace_codes.split(',') if nace_codes else []
    location_list = location.split(',') if location else []

    if location_option == "Gemeente":
        option_int = 1
    elif location_option == "Gemeente en buurgemeenten":
        option_int = 2
    else:
        option_int = 3

    kbo_scraper(location_list, nace_codes_list, option_int)
    geo_json = geo_coding()
    print(geo_json)
    geojson_str = json.dumps(geo_json)

    # HTML inhoud met geïnjecteerde GeoJSON data
    html_content = f"""
    <html>
    <head>    
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        
            <script>
                L_NO_TOUCH = false;
                L_DISABLE_3D = false;
            </script>
        
        <style>html, body {{width: 100%;height: 100%;margin: 0;padding: 0;}}</style>
        <style>#map {{position:absolute;top:0;bottom:0;right:0;left:0;}}</style>
        <script src="https://cdn.jsdelivr.net/npm/leaflet@1.6.0/dist/leaflet.js"></script>
        <script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.6.0/dist/leaflet.css"/>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css"/>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css"/>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css"/>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css"/>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
        <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster-src.js"></script>
        <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
        
                <meta name="viewport" content="width=device-width,
                    initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
                <style>
                    #map {{
                        position: relative;
                        width: 100.0%;
                        height: 100.0%;
                        left: 0.0%;
                        top: 0.0%;
                    }}
                </style>
            
    </head>
    <body>    
        <label for="naceFilter">Filter by Nace Code:</label>
        <select id="naceFilter" onchange="filterMarkers()">
            <option value="all">All</option>
        </select>
        <div class="folium-map" id="map" ></div>
            
    </body>
    <script>    
        
        var map = L.map("map", {{
            center: [50.8742245, 4.726316],
            crs: L.CRS.EPSG3857,
            zoom: 13,
            zoomControl: true,
            preferCanvas: false,
        }});

        L.tileLayer(
            "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
            {{"detectRetina": false, "maxNativeZoom": 18, "maxZoom": 18, "minZoom": 0, "noWrap": false, "opacity": 1, "subdomains": "abc", "tms": false}}
        ).addTo(map);

        function loadMarkers(geojsonData) {{
            // Verwijder eerst alle bestaande markers uit de cluster groep
            markers = L.markerClusterGroup();
            clearMarkers();

            // Functie om een marker toe te voegen voor elk feature in de GeoJSON data
            function onEachFeature(feature, layer) {{
                if (feature.properties) {{
                    var popupContent = "<b>Bedrijfsnaam:</b> " + feature.properties.company_name;
                    popupContent += "<br><b>Adres:</b> " + feature.properties.address;
                    popupContent += "<br><b>Ondernelers nummer:</b> " + feature.properties.company_nr;
                    popupContent += "<br><b>Omzet:</b> " + feature.properties.revenue;
                    popupContent += "<br><b>Werknemers:</b> " + feature.properties.employee_nr;
                    layer.bindPopup(popupContent);
                }}
            }}

            // Voeg markers toe aan de cluster groep
            L.geoJSON(geojsonData, {{
                onEachFeature: onEachFeature
            }}).addTo(markers);

            // Voeg de marker cluster groep toe aan de kaart
            map.addLayer(markers);
            map.fitBounds(markers.getBounds());
        }}

        function clearMarkers() {{
            if (markers) {{
                console.log("*****")
                map.removeLayer(markers);
            }}
            markers = L.markerClusterGroup();
        }}

        var geojsonData = {geojson_str};
        loadMarkers(geojsonData);
                
        
    </script>
    </html>     
    """

    m = folium.Map()
    plugins.Fullscreen().add_to(m)
    plugins.Draw().add_to(m)
    m.save('map.html')

    return f"""<iframe style="width: 100%; height: 480px" name="result" allow="midi; geolocation; microphone; camera; 
    display-capture; encrypted-media;" sandbox="allow-modals allow-forms 
    allow-scripts allow-same-origin allow-popups 
    allow-top-navigation-by-user-activation allow-downloads" allowfullscreen="" 
    allowpaymentrequest="" frameborder="0" srcdoc='{html_content}'></iframe>"""


# Gradio interface
iface = gr.Interface(
    fn=run_scraper,
    inputs=[
        gr.Textbox(label="Nacebelcode(s) (comma-separated)"),
        gr.Radio(choices=["Gemeente", "Gemeente en buurgemeenten", "Postcode"], label="Locatie"),
        gr.Textbox(label="Zoeken (comma-separated)")
    ],
    outputs="html",
    title="KBO Scraper Interface",
    description="Enter NACE codes, and choose a location option to run the KBO scraper."
)

# Running the interface
iface.launch()
