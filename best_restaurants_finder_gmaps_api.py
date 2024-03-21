import os
import googlemaps
from ppprint import ppprint
import pandas as pd
import numpy as np
import time
import sys
from dotenv import load_dotenv, find_dotenv
import streamlit as st


pd.set_option('display.float_format', lambda x: '%.2f' % x)
pd.set_option('display.max_columns', None)

# Path
dotenv_path = 'C:\\Users\\kevin\\Google Drive\\My Drive\\Github\\all-api-keys\\.env'
load_dotenv(dotenv_path)

# Load api key
gmaps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(gmaps_api_key)

import warnings
# Set ignore_warnings to True
warnings.simplefilter("ignore")

def find_best_restaurants(city_name, place_type, min_rating=0, min_n_ratings=0, query='', n_meters=1000):
  lat = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lat')
  lng = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lng')
  df = pd.DataFrame()
  min_rating = min_rating
  min_n_ratings = min_n_ratings
  next_page_token_list = ['', '', '']
  # print(len(next_page_token_list))
  counter = 1

  for i in range(len(next_page_token_list)):
    parent_results = gmaps.places(location=(lat,lng),
                                  type = place_type,
                                  query = query,
                                  radius = n_meters,
                                  page_token = next_page_token_list[i],
                                  # minprice = minprice,
                                  # maxprice = maxprice
                                  )
    results = parent_results.get('results')

    for j in range(len(results)):
      if results[j].get('user_ratings_total') >= min_n_ratings and results[j].get('rating') >= min_rating:
        # df = df.concat(results[j], ignore_index=True)
        df = df._append(results[j], ignore_index=True)
    try:
      next_page_token_list[counter] = parent_results.get('next_page_token')
      print(next_page_token_list)
      counter += 1
      time.sleep(3)
    except:
      time.sleep(0)

  df = df.join(pd.json_normalize(df['geometry'])).drop('geometry',axis=1)
  df = df.sort_values(by=['rating', 'user_ratings_total'], ascending=[False, False])
  df = df[ ['name', 'rating', 'user_ratings_total'] + [ col for col in df.columns if col != ['name', 'rating', 'user_ratings_total'] ] ]
  print(str(len(df)) + " results")
  return df

# Put the sub-city into the city_name for it to work better. Eg. Lower East Side instead of Manhattan.
find_best_restaurants(city_name='San Jose',
                      # place_type is more set in stone, has to be allowed param in google
                      place_type='restaurant',
                      min_rating=4.3,
                      min_n_ratings=100,
                      # can be park, asian, bar, etc.
                      # query='asian',
                      # radius is in meters, so 4828.02 = 3 miles.
                      n_meters =1000,
                      )

# Verify there are 60 results
# find_best_restaurants('morgan hill', 'restaurant')

# # Define search parameters
# city_name = 'North San Jose'

# lat = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lat')
# lng = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lng')

# search_params = {
#     'location': str(lat)+','+str(lng),  # Define the location you want to search near
#     'radius': 1000,                   # Radius in meters
#     'keyword': 'restaurant',          # Keyword for the search (e.g., 'restaurant')
#     'minprice': 0,                   # Minimum price level
#     'maxprice': 4,                   # Maximum price level
# }

# # Perform the search
# places = gmaps.places_nearby(**search_params)

# # Filter and sort results
# filtered_places = [place for place in places['results'] if place['user_ratings_total'] >= 100 and place['rating'] >= 4.1]
# sorted_places = sorted(filtered_places, key=lambda x: x['name'])  # Sort by restaurant name

# # Display the top 10 results
# top_10_places = sorted_places[:10]
# for place in top_10_places:
#     print(f"Name: {place['name']}, Rating: {place['rating']}, Total Reviews: {place['user_ratings_total']}")



