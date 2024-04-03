import os
import googlemaps
from ppprint import ppprint
import pandas as pd
import numpy as np
import time
import sys
from dotenv import load_dotenv, find_dotenv
import streamlit as st
from datetime import datetime
import numpy as np

# pd.set_option('display.float_format', lambda x: '%.2f' % x)
# pd.set_option('display.max_columns', None)

# Path
dotenv_path = 'C:\\Users\\kevin\\Google Drive\\My Drive\\Github\\all-api-keys\\.env'
load_dotenv(dotenv_path)

# Load api key
gmaps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(gmaps_api_key)

# Set Title tag of Streamlit link
st.set_page_config(page_title="Kevin's Best Restaurants Finder")
                   # Blocked: layout="wide")

# import warnings
# Set ignore_warnings to True
# warnings.simplefilter("ignore")

# Assign points with exponential decay.
def create_points_column(df, column_name):
    # Define bins and labels
    bins = [0, 100, 300, 800, 2000000]
    labels = [1, 2, 3, 3.5]  # Points assigned for each bin
    
    # Check if the column exists and then generate the points series
    if column_name in df.columns:
        return pd.cut(df[column_name], bins=bins, labels=labels, right=False, include_lowest=True)
    else:
        return "Column name provided does not exist in DataFrame."

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
      if counter < len(next_page_token_list):
        next_page_token_list[counter] = parent_results.get('next_page_token')
        # Comment out for streamlit
        # print(next_page_token_list)
        counter += 1
        time.sleep(3)
      else:
         break
    except KeyError:
      break

  # Expands this into try/except:
  # df = df.join(pd.json_normalize(df['geometry'])).drop('geometry',axis=1)

  # Kill the whole thing if no results found.
  if df.empty:
        raise ValueError("You have high af standards. Unfortunately, there are no results matching the criteria. Please lower minimum number of reviews or minimum rating.")
  else:
      # Attempt to normalize and join the 'geometry' column
      expanded_geometry = pd.json_normalize(df['geometry'])
      df = df.join(expanded_geometry).drop('geometry', axis=1)

      # Todo: Figure out the best way to create a score column
      # Create permalink with long/lat/place_id

      df['permalink'] = df.apply(lambda row: f"https://www.google.com/maps/search/?api=1&query={row['location.lng']}%2C{row['location.lat']}&query_place_id={row['place_id']}"
                                , axis=1)
      
      # Add score column
      df['user_ratings_adjusted'] = create_points_column(df, 'user_ratings_total')
      df['user_ratings_adjusted'] = pd.to_numeric(df['user_ratings_adjusted'])
      df['score'] = df['rating']*df['user_ratings_adjusted']

      # Sort by rating and user rating, reset index.
      df = df.sort_values(by=['score', 'user_ratings_total'], ascending=[False, False])
      # df = df.sort_values(by=['rating', 'user_ratings_total'], ascending=[False, False])
      # Set column order
      col_order = ['name', 'score', 'rating', 'user_ratings_total', 'permalink', 'price_level']
      # Do not repeat the col names
      df = df[col_order + [col for col in df.columns if col not in col_order]]
      #   df = df[ ['name', 'rating', 'user_ratings_total'] + [ col for col in df.columns if col != ['name', 'rating', 'user_ratings_total'] ] ]
        # Comment out for streamlit
      #   print(str(len(df)) + " results")
        #   return df
      # Final drop duplicates check, based on place_id.
      df = df.drop_duplicates(subset='place_id', keep='first')
      # Final reset index
      df = df.reset_index(drop=True)
      return df


# From streamlit
def app():
    st.title("Best Restaurants Finder")
    st.caption("Are you sick of finding 5 star restaurants with 1 review? \
               This app lets you filter for the highest rated restaurants only if they have a minimum number of reviews.")
    with st.form(key='my_form'):
        city_name = st.text_input(
            "Which city are you looking for a restaurant in:"
            ,max_chars=100
            ,type="default"
            ,placeholder="Enter a city"
        )
        options = ["restaurant", "cafe", "bar", "park", "bakery"]
                   # "night_club", "art_gallery", "museum", "beauty_salon"]
        place_type = st.selectbox("Place type: ", options)
        # min_rating = st.number_input('Insert desired minimum rating between 0 and 5 (eg. 4.3)'
        #                              ,placeholder="4.3"
        #                              )
        # Create a list of numbers from 0 to 4 with a step of 0.5
        numbers_5_to_4 = np.round(np.arange(4.9, 3.6, -0.1), 1)
        numbers_4_to_0 = np.round(np.arange(3.5, -0.1, -0.5), 1)
        combined_numbers = sorted(np.unique(np.concatenate((numbers_5_to_4, numbers_4_to_0))), reverse=True)
        min_rating = st.selectbox('Desired Minimum Rating?'
                                     ,combined_numbers
                                     ,index = 6 # Default is 4.3 stars.
                                     )
        # Repeat for n_reviews
        numbers_0_to_200 = np.arange(0, 201, 50)
        numbers_200_to_1000 = np.arange(200, 1001, 100)
        combined_reviews_numbers = np.unique(np.concatenate((numbers_0_to_200, numbers_200_to_1000)))
        
        min_num_reviews = st.selectbox('Desired Minimum Amount of Reviews?'
                                    ,combined_reviews_numbers
                                    # Default is 100
                                    ,index = 2)
        # min_num_reviews = st.number_input('Insert desired minimum number of reviews (eg. 100)'
        #                             ,placeholder="500")

        cuisine_type = st.text_input(
            "[Optional] Enter type of cuisine you're looking for: "
            ,max_chars=100
            ,type="default"
            ,placeholder="Eg. asian, boba, noodles, sushi, japanese, italian, german"
        )

        price_level_options = {
            "No label": None,
            "$": 1,
            "$$": 2,
            "$$$": 3,
            "$$$$": 4
        }
        price_level_type = st.multiselect("[Optional] Price levels to include: (Default is All)", 
                                          options=list(price_level_options.keys()),
                                          default=list(price_level_options.keys()))

        if st.form_submit_button("Submit"):
            try:
              with st.spinner(f'Generating top ' + next(iter({place_type})) + 's...'):
              # if cuisine_type is not blank:
              # with st.spinner(f'Generating top ' + next(iter({place_type})) + 's (with a ' + next(iter({cuisine_type})) + ' focus)...'):
                  # Put the sub-city into the city_name for it to work better. Eg. Lower East Side instead of Manhattan.
                  df = find_best_restaurants(city_name=city_name,
                        # place_type is more set in stone, has to be allowed param in google
                        place_type=place_type,
                        min_rating=min_rating,
                        min_n_ratings=min_num_reviews,
                        # can be park, asian, bar, etc.
                        query=cuisine_type,
                        # radius is in meters, so 4828.02 = 3 miles.
                        n_meters=1000,
                        )
                  
                  # Filter rows only if df['price_level'] in price_level_type
                  # Step 1: Translate selected keys to their corresponding values
                  selected_values = [price_level_options[key] for key in price_level_type]

                  # Step 2: Filter DataFrame rows
                  filtered_df = df[df['price_level'].isin(selected_values)]

                  # Exception handling: if there are no restaurants > 1000 reviews, return this.
                  if filtered_df.empty:
                        # If the dataframe is empty, raise a custom exception
                        raise ValueError("No restaurants found that match the criteria.")
                  
                  # Reset index before returning results
                  filtered_df = filtered_df.reset_index(drop=True)

                  return st.dataframe(filtered_df,
                                      column_config={
                                         "permalink": st.column_config.LinkColumn(
                                            "Gmaps Link", 
                                            help="Direct link to Google Maps",
                                            display_text="GMaps Link"
                                         )
                                         ,"score": st.column_config.ProgressColumn(
                                              "Adjusted Score",
                                              help="Adjusted score",
                                              format="%.1f",
                                              min_value=0,
                                              max_value=5*3.5,
                                          )
                                          ,"price_level": st.column_config.ProgressColumn(
                                              "Price",
                                              format="%.0f",
                                              min_value=0,
                                              max_value=4,
                                          )
                                          # ,"photos": st.column_config.ImageColumn(
                                          #       "Images",
                                          #   )
                                        # "permalink": st.column_config.LinkColumn()
                  })
            except ValueError as e:
                # Catch the custom exception and inform the user
                st.error(str(e))
                # st.info("There are no results given your input criteria. Please adjust it and try again.")
      

# Only run this if its ran as a standalone program.
if __name__ == '__main__':
    app()