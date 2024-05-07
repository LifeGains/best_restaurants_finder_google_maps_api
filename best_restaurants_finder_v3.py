# Google Api Source: https://developers.google.com/maps/documentation/places/web-service/search-nearby
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
from pandas import json_normalize
import requests
import json
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
import inspect
from geopy.distance import geodesic

# pd.set_option('display.float_format', lambda x: '%.2f' % x)
# pd.set_option('display.max_columns', None)

# Path
dotenv_path = 'C:\\Users\\kevin\\Google Drive\\My Drive\\Github\\all-api-keys\\.env'
load_dotenv(dotenv_path)

# Load api key
gmaps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
abstract_api_key = os.getenv("ABSTRACT_API")
gmaps = googlemaps.Client(gmaps_api_key)

# Set Title tag of Streamlit link
st.set_page_config(page_title="Kevin's Best Restaurants Finder")
                   # Blocked: layout="wide")

# import warnings
# Set ignore_warnings to True
# warnings.simplefilter("ignore")

def get_city_bounds(latitude, longitude):
    # Initialize Nominatim API
    geolocator = Nominatim(user_agent="best-restaurants-finder")

    # Use reverse geocoding to get an address from latitude and longitude
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    print(location)
    if location:
        address = location.raw['address']
        city = address.get('city', address.get('town', address.get('village')))
        if city:
            # Get the bounding box for the city
            location = geolocator.geocode(city)
            if location:
                return {
                    'city': city,
                    'bounding_box': location.raw['boundingbox']
                }
            else:
                return {'error': 'City bounds could not be determined.'}
        else:
            return {'error': 'City not found.'}
    else:
        return {'error': 'Location not found.'}
    
# Assign points with exponential decay.
def create_points_column(df, column_name):
    # Define bins and labels
    bins = [0, 100, 500, 800, 2000000]
    labels = [1, 2, 2.25, 2.5]  # Points assigned for each bin
    
    # Check if the column exists and then generate the points series
    if column_name in df.columns:
        return pd.cut(df[column_name], bins=bins, labels=labels, right=False, include_lowest=True)
    else:
        return "Column name provided does not exist in DataFrame."

# Initialize empty token_list
token_list = []
# Initialize master_Df
master_df = pd.DataFrame()

def find_best_restaurants(city_name, place_type, lat, lng, west,east,south,north, prices_allowed=[None,1,2,3,4], query='', 
                          open_now_boolean=False, page_token="", master_df=master_df,
                          ):
# Using Streamlit Geolocation Package
# st.write("Using your current location. Please click Allow:")
# location = streamlit_geolocation()
# lat = location['latitude']
# lng = location['longitude']

# # Using Abstract API
# response = requests.get(f"https://ipgeolocation.abstractapi.com/v1/?api_key={abstract_api_key}")
# # Make sure status code is 200.
# print(f"Status Code: {response.status_code}")
# # Assuming response.content is a JSON string in bytes format
# content_dict = json.loads(response.content.decode('utf-8'))
# lat = float(content_dict.get('latitude'))
# lng = float(content_dict.get('longitude'))

# Using Geocoder API
# g = geocoder.ip('me')
# lat, lng = g.latlng
#   if lat == "" or lng == "":
    # Automatic Parameters
    # lat = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lat')
    # lng = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lng')
  
  # Filter out None values from prices_allowed and calculate the maximum of the remaining values
  filtered_prices = [price for price in prices_allowed if price is not None]
  max_price = max(filtered_prices) if filtered_prices else None
  min_price = min(filtered_prices) if filtered_prices else None

  # location_string = "rectangle:" + str(south) + "," + str(west) + "|" + str(north) + "," + str(east)
  # Calculate ideal radius
  # Calculate the midpoint of the bounding box to use as a circle center
  midpoint = ((south + north) / 2, (west + east) / 2)

  # Calculate distances for width (east to west) and height (north to south) of the bounding box
  width = geodesic((midpoint[0], west), (midpoint[0], east)).meters
  height = geodesic((south, midpoint[1]), (north, midpoint[1])).meters

  # The diameter is the max of the width or height
  diameter = max(width, height)

  # The radius is half the diameter
  # Im dividing it by 4 cuz its still too big.
  ideal_radius = int(diameter / 6)
  print("Ideal radius: " + str(ideal_radius))

  # Rankby distance when query is not null
  if query != "":
      rank_by_variable = 'distance'
  else:
      rank_by_variable = ''
  gmaps_json = gmaps.places(location=(lat,lng),
                            radius = ideal_radius,
                            # rankby = rank_by_variable,
                            type = place_type,
                            query = query,
                            min_price = min_price,
                            max_price = max_price,
                            open_now = open_now_boolean,
                            page_token = page_token,
                            )

  # Dataframe-ize results
  df = json_normalize(gmaps_json)
  # display(df)

  # Handle if 0 results returns:
  if df['status'].iloc[0] == 'ZERO_RESULTS':
    raise ValueError(f"You have high af standards for {city_name}. Unfortunately, there are no results matching the criteria. Is it because you have Open Now checked? Please lower minimum number of reviews or minimum rating.")

  # If df['next_page_token'] exists
    # append df['next_page_token'].value to token_list
  if 'next_page_token' in df and pd.notna(df['next_page_token'].iloc[0]):
    # Append the value of 'next_page_token' to token_list
    next_page_token = df['next_page_token'].iloc[0]
    token_list.append(next_page_token)
    # Show results in dataframe
    # Explode the results into same level row
    df2 = json_normalize(df['results'].explode())
    # display(df2)
    # Explode photos too
    df3 = json_normalize(df2['photos'].explode())
    df4 = pd.concat([df2.drop('photos', axis=1), df3], axis=1)

    # display(df4)
    # Append dataframe to master dataframe
    master_df = pd.concat([master_df, df4], axis=0).reset_index(drop=True)
    # Ensure a short delay before the next request to comply with API's "next_page_token" latency
    time.sleep(2)  # Google Maps API requires a short delay before using the next_page_token
    return find_best_restaurants(city_name, place_type, lat, lng,  west,east,south,north, prices_allowed, query, open_now_boolean, next_page_token, master_df=master_df)

  # No 'next_page_token' means its already the last page.
  else:
    # Explode the results into same level row
    df2 = json_normalize(df['results'].explode())
    # display(df2)
    # Explode photos too
    df3 = json_normalize(df2['photos'].explode())
    df4 = pd.concat([df2.drop('photos', axis=1), df3], axis=1)

    # Append dataframe to master dataframe
    master_df = pd.concat([master_df, df4], axis=0).reset_index(drop=True)
    # print(len(master_df))
    
    # Checks
    # Check and remove any duplicates
    master_df = master_df.drop_duplicates(subset='place_id', keep='first')
    # print(len(master_df))
    
    master_df = do_stuff_to_alrd_outputted_gmaps_df(master_df)

    return master_df

def do_stuff_to_alrd_outputted_gmaps_df(df):

    # Add permalink column ith long/lat/place_id
    df['permalink'] = df.apply(
        lambda row: f"https://www.google.com/maps/search/?api=1&query={row['geometry.location.lng']}%2C{row['geometry.location.lat']}&query_place_id={row['place_id']}"
        , axis=1)

    # Add score column
    df['user_ratings_adjusted'] = create_points_column(df, 'user_ratings_total')
    df['user_ratings_adjusted'] = pd.to_numeric(df['user_ratings_adjusted'])
    df['score'] = df['rating']*df['user_ratings_adjusted']

    # Sort by score and number reviews
    df = df.sort_values(by=['score', 'user_ratings_total'], ascending=[False, False])
    # df = df.sort_values(by=['rating', 'user_ratings_total'], ascending=[False, False])
    # Set column order
    col_order = ['name', 'permalink', 'score', 'rating', 'user_ratings_total', 'price_level']
    # Put important columns in the front and do not repeat them in the back. 
    df = df[col_order + [col for col in df.columns if col not in col_order]]

    # Final drop duplicates check, based on place_id.
    #   df = df.drop_duplicates(subset='place_id', keep='first')

    # Final reset index
    df = df.reset_index(drop=True)

    return df

# From streamlit
def app():
    st.title("Best Restaurants Finder")
    st.caption("Are you sick of finding 5 star restaurants with 1 review? \
               This app lets you filter for the highest rated restaurants only if they have a minimum number of reviews.")
    location_boolean = False
    if st.toggle('Use current location?'):
        # location = get_geolocation()
        # location_boolean = True
        with st.spinner('Fetching your location...'):
            try:
                location = get_geolocation()
                location_boolean = True
                st.success('Location fetched successfully!')
            except Exception as e:
                st.error(f'Failed to fetch location: {e}')

    with st.form(key='my_form'):
        city_name = st.text_input(
            "Enter a City or Leave Blank for current location: "
            ,max_chars=100
            ,type="default"
            ,placeholder="Eg. San Francisco, Miami"
        )
        options = ["restaurant", "cafe", "bar", "bakery"]
                   # "night_club", "art_gallery", "museum", "beauty_salon"]

        place_type = st.selectbox("Place Type: ", options)
        # min_rating = st.number_input('Insert desired minimum rating between 0 and 5 (eg. 4.3)'
        #                              ,placeholder="4.3"
        #                              )
        # Create a list of numbers from 0 to 4 with a step of 0.5
        numbers_5_to_4 = np.round(np.arange(4.9, 3.6, -0.1), 1)
        numbers_4_to_0 = np.round(np.arange(3.5, -0.1, -0.5), 1)
        combined_numbers = sorted(np.unique(np.concatenate((numbers_5_to_4, numbers_4_to_0))), reverse=True)
        min_rating = st.selectbox('Min Rating?'
                                     ,combined_numbers
                                     ,index = 6 # Default is 4.3 stars.
                                     )
        # Repeat for n_reviews
        numbers_0_to_200 = np.arange(0, 201, 50)
        numbers_200_to_1000 = np.arange(200, 1001, 100)
        combined_reviews_numbers = np.unique(np.concatenate((numbers_0_to_200, numbers_200_to_1000)))
        
        min_num_reviews = st.selectbox('Min Amount of Reviews?'
                                    ,combined_reviews_numbers
                                    # Default is 100
                                    ,index = 2)
        # min_num_reviews = st.number_input('Insert desired minimum number of reviews (eg. 100)'
        #                             ,placeholder="500")

        # Create open now toggle
        open_now_boolean = st.toggle('Must be Open Now?',
                                    value=False)
        
        with st.expander("Additional Options:"):
            cuisine_list = [
                "American",
                "Italian",
                "Mexican",
                "Chinese",
                "Japanese",
                "Indian",
                "Thai",
                "French",
                "Mediterranean",
                "Greek",
                "Spanish",
                "Korean",
                "Vietnamese",
                "Middle Eastern",
                "Caribbean",
                "Brazilian",
                "German",
                "British",
                "Cajun",
                "Soul Food",
                "Southern",
                "Tex-Mex",
                "Peruvian",
                "Argentinian",
                "Turkish",
                "Russian",
                "Filipino",
                "African",
                "Moroccan",
                "Ethiopian",
                "Australian",
                "Hawaiian",
                "Irish",
                "Swedish",
                "Belgian",
                "Portuguese",
                "Israeli",
                "Lebanese",
                "Indonesian",
                "Malaysian",
                "Singaporean",
                "Scandinavian",
                "Polish",
                "Cuban",
                "Jamaican",
                "Nigerian",
                "Kenyan",
                "Tanzanian",
                "South African",
                "Canadian",
                "New Zealand",
                "Fusion",
                "Boba",
                "Noodles",
                "Asian",
                "Coffee",
                "Tea",
                "Brunch",
                "Pizza",
                "Burger",
                "Pasta",
                "Sushi",
                "Tacos",
                "Steak",
                "Chicken Tikka Masala",
                "Ramen",
                "Pho",
                "Pad Thai",
                "Lasagna",
                "Sushi",
                "Curry",
                "Hamburger",
                "Fried Chicken",
                "Burrito",
                "Fish",
                "Salmon",
                "Shrimp",
                "Salad",
                "Sashimi",
                "Poke Bowl",
                "Risotto",
                "Gyoza",
                "Dim Sum",
                "Samosa",
                "Croissant",
                "Bagel",
                "Donut",
                "Ice Cream",
                "Chocolate Cake",
                "Apple Pie",
                "Cheesecake",
                "Tiramisu",
                "Mango Sticky Rice",
                "Baklava",
                "Pierogi",
                "Goulash",
                "Peking Duck",
                "Paella",
                "Ceviche",
                "Gyros",
                "Falafel",
                "Biryani",
                "Chili Con Carne",
                "Beef Stroganoff",
                "Moussaka",
                "Pancakes",
                "Waffles",
                "Crepes",
                "Fries",
                "Fast Food"
            ]
            cuisine_type = st.selectbox("Cuisine Type: "
                                        , cuisine_list
                                        , index=None
                                        , placeholder="Eg. asian, boba, italian, sushi")
            # cuisine_type = st.text_input(
            #     "[Optional] Enter type of cuisine you're looking for: "
            #     ,max_chars=100
            #     ,type="default"
            #     ,placeholder="Eg. asian, boba, italian, sushi"
            # )

            price_level_options = {
                "No label": None,
                "$": 1,
                "$$": 2,
                "$$$": 3,
                "$$$$": 4
            }
            price_level_type = st.multiselect("Cost: (Default is All)", 
                                            options=list(price_level_options.keys()),
                                            default=list(price_level_options.keys()))
            
            # Convert selected price level symbols to their corresponding numeric values
            prices_allowed = [price_level_options[price] for price in price_level_type if price in price_level_options]

        customized_button = st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #578a00;
                color:#ffffff;
            }
            div.stButton > button:hover {
                background-color: #00128a;
                color:#ffffff;
                }
            </style>""", unsafe_allow_html=True)
        submit_btn = customized_button  # Modified
        submit_btn = st.form_submit_button('Submit')
        
        # if st.form_submit_button("Submit"):
        if submit_btn:
            try:
                with st.spinner(f'Generating top ' + next(iter({place_type})) + 's...'):
                # if cuisine_type is not blank:
                # with st.spinner(f'Generating top ' + next(iter({place_type})) + 's (with a ' + next(iter({cuisine_type})) + ' focus)...'):
                    if location_boolean == False and city_name == "":
                        raise ValueError(f"Please enter a city name or turn on current location toggle.")

                    # Put the sub-city into the city_name for it to work better. Eg. Lower East Side instead of Manhattan.                    
                    if location_boolean:
                        lat_coord = location['coords']['latitude']
                        lng_coord = location['coords']['longitude']
                    else:
                        lat_coord = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lat')
                        lng_coord = gmaps.places(query=city_name).get('results')[0].get('geometry').get('location').get('lng')
                    print(lat_coord)
                    print(lng_coord)

                    # Obtain the bounding box coordinates as strings
                    city_bounding_box = get_city_bounds(lat_coord, lng_coord)['bounding_box']
                    print(city_bounding_box)
                    # Cast the bounding box coordinates to floats
                    south_coord, north_coord, west_coord, east_coord = map(float, city_bounding_box)

                    df = find_best_restaurants(
                        city_name=city_name, 
                        place_type=place_type, 
                        prices_allowed=prices_allowed, 
                        query=cuisine_type, 
                        open_now_boolean=open_now_boolean, 
                        lat=lat_coord,
                        lng=lng_coord,
                        west=west_coord,
                        east=east_coord,
                        south=south_coord,
                        north=north_coord,
                        )

                    # print(prices_allowed)

                    # Add user specified filters
                    df = df[df['rating'] >= min_rating]
                    df = df[df['user_ratings_total'] >= min_num_reviews]

                    # Exception handling: if there are no restaurants > 1000 reviews, return this.
                    if df.empty:
                        # If the dataframe is empty, raise a custom exception
                        raise ValueError(f"You have high af standards for {city_name}. Unfortunately, there are no results matching the criteria. Is it because you have Open Now checked? Please lower minimum number of reviews or minimum rating.")
                    
                    # Reset index before returning results
                    df = df.reset_index(drop=True)

                    # Show resulting dataframe
                    return st.dataframe(df,
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
                                                max_value=5*2.5,
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
      
# Inspect parameters
# Get the parameters of the function
parameters = inspect.signature(gmaps.places).parameters
# Extract parameter names
parameter_names = list(parameters.keys())
# Print the parameter names
# print("Function parameters:", parameter_names)

# Only run this if its ran as a standalone program.
if __name__ == '__main__':
    app()