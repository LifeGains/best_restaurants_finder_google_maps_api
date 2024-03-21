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
      # Comment out for streamlit
    #   print(next_page_token_list)
      counter += 1
      time.sleep(3)
    except:
      time.sleep(0)

  df = df.join(pd.json_normalize(df['geometry'])).drop('geometry',axis=1)
  df = df.sort_values(by=['rating', 'user_ratings_total'], ascending=[False, False])
  # Do not repeat the col names
  df = df[['name', 'rating', 'user_ratings_total'] + [col for col in df.columns if col not in ['name', 'rating', 'user_ratings_total']]]
#   df = df[ ['name', 'rating', 'user_ratings_total'] + [ col for col in df.columns if col != ['name', 'rating', 'user_ratings_total'] ] ]
    # Comment out for streamlit
#   print(str(len(df)) + " results")
    #   return df
  return df

# From streamlit
def app():
    st.title("Best Restaurants Finder")
    st.caption("Are you sick of finding 5 star restaurants with 1 review? \
               This app lets you filter for the highest rated restaurants only if they have a minimum number of reviews.")
    with st.form(key='my_form'):
        city_name = st.text_input(
            "Enter the city from which you want to find a restaurant"
            ,max_chars=100
            ,type="default"
            ,placeholder="Enter a city"
        )
        options = ["restaurant", "bar", "cafe", "bakery", "night_club"]
                   # art_gallery", "museum", "beauty_salon"]
        place_type = st.selectbox("Choose a place type", options)
        min_rating = st.number_input('Insert desired minimum rating between 0 and 5 (eg. 4.3)'
                                     ,placeholder="4.3"
                                     )
        min_num_reviews = st.number_input('Insert desired minimum number of reviews (eg. 100)'
                                    ,placeholder="500")

        if st.form_submit_button("Submit"):
            with st.spinner('Generating top restaurants...'):
                # Put the sub-city into the city_name for it to work better. Eg. Lower East Side instead of Manhattan.
                df = find_best_restaurants(city_name=city_name,
                      # place_type is more set in stone, has to be allowed param in google
                      place_type=place_type,
                      min_rating=min_rating,
                      min_n_ratings=min_num_reviews,
                      # can be park, asian, bar, etc.
                      # query='asian',
                      # radius is in meters, so 4828.02 = 3 miles.
                      n_meters=1000,
                      )
                return st.dataframe(df)
        
    if not city_name or not place_type:
        st.info("Please enter a valid city or select a valid place type.")



    
# Only run this if its ran as a standalone program.
if __name__ == '__main__':
    app()