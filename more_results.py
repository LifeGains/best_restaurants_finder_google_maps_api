# Nope, as of 3/28/24 this still only produces max of 60 results.

import googlemaps
from time import sleep
import pandas as pd
import os
from ppprint import ppprint
import pandas as pd
import numpy as np
import time
import sys
from dotenv import load_dotenv, find_dotenv
import streamlit as st

def format_res(results):
    # Extracting and formatting the results
    formatted_results = [{
        "lat": res["geometry"]["location"]["lat"],
        "long": res["geometry"]["location"]["lng"],
        "name": res.get("name"),
        "place_id": res.get("place_id")
    } for res in results]
    return pd.DataFrame(formatted_results)

def do_search(gmaps, place_type, location, radius, page_token=None):
    # Performing a search with the Google Maps client
    return gmaps.places_nearby(location=location, type=place_type, radius=radius, page_token=page_token)

def full_search(place_type, key, location, radius):
    gmaps = googlemaps.Client(key=key)
    is_another_page = True
    page_token = None
    df = pd.DataFrame(columns=["lat", "long", "name", "place_id"])
    
    while is_another_page:
        res = do_search(gmaps, place_type, location, radius, page_token)
        if res["status"] == "OK":
            df = pd.concat([df, format_res(res["results"])], ignore_index=True)
            page_token = res.get("next_page_token")
            is_another_page = bool(page_token)
            if is_another_page:
                sleep(3)  # Sleep before the next call due to API limitations
        else:
            print(f"{res['status']} for {location}")
            break
    return df

# Example usage
# Path
dotenv_path = 'C:\\Users\\kevin\\Google Drive\\My Drive\\Github\\all-api-keys\\.env'
load_dotenv(dotenv_path)

# Load api key
key = os.getenv("GOOGLE_MAPS_API_KEY")
# gmaps = googlemaps.Client(gmaps_api_key)
# key = "YOUR_API_KEY"  # Replace with your API key
lst_results = []

# Inputs --------------------------------------------
place_type = "store"
radius = 1000
coords = [
    # First two are just tests for error handling if there are 0 results.
    # "14.5446147628533, -90.84266666418",
    # "14.5538523714673, -90.84266666418",
    "-37.816660, 144.967092"
]

for coord in coords:
    location = [float(x) for x in coord.split(",")]
    df_result = full_search(place_type, key, location, radius)
    lst_results.append(df_result)

# Example of displaying the head of the first result DataFrame
if lst_results:
    print(lst_results[0].head())
    print("Total Length: " + str(len(lst_results[0])))
