import requests
from dotenv import load_dotenv
import os
import json
from pprint import pprint
import pandas as pd

pd.set_option('display.max_columns', None)

# Load the .env file
env_path = r"C:\Users\kevin\Downloads\github_nextjs\all-api-keys\.env"
load_dotenv(env_path)

# Retrieve the Yelp API key
api_key = os.getenv("YELP_API_KEY")
if not api_key:
    raise ValueError("API key not found. Ensure YELP_API_KEY is set in the .env file.")

# Define the API request
url = "https://api.yelp.com/v3/businesses/search"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {api_key}",  # Add the API key in the Authorization header
}

# Query parameters (including location)
params = {
    "term": "restaurants",
    "categories": "asian",
    "location": "San Jose, CA",  # Specify the location here
    "limit": 50,
    "radius": 14000 # in meters. = a 10 mile radius
    # offset Offset for pagination (e.g., 20 for the second page of results).
    # sort_by [best_match, rating, review_count, distance]
    # price [1,2,3,4]
    # open_now boolean
}

# Make the request
response = requests.get(url, headers=headers, params=params)

# Parse the JSON response
response_json = json.loads(response.text)

# Extract businesses and create a DataFrame
if "businesses" in response_json:
    businesses = response_json["businesses"]

    data = []
    for business in businesses:
        # # What keys are avail?
        # print(business.keys())
        # break;
        
        # Extract the required attributes
        data.append({
            "id": business.get("id"),
            "name": business.get("name"),
            "review_count": business.get("review_count"),
            "rating": business.get("rating"),
            "url": business.get("url"),
            "city": business.get("location", {}).get("city"),
            "is_closed": business.get("is_closed")
        })
    
    # Create the DataFrame
    df = pd.DataFrame(data)

    # Create custom total scoring
    df['review_count_tiers'] = pd.cut(
        df['review_count'],
        bins=[0, 100, 300, 700, float('inf')],
        labels=[0, 1, 2, 3],  # Assign tier values
        right=False
    )

    df['rating_tiers'] = pd.cut(
        df['rating'],
        bins=[0, 3.8, 4.0, 4.2, 4.5, float('inf')],
        labels=[0, 0.5, 1, 2, 3],  # Assign tier values
        right=False
    )

    # Calculate the total score
    df['score'] = df['review_count_tiers'].astype(float) * df['rating_tiers'].astype(float)

    # Move 'score' to the 3rd column
    score_column = df.pop('score')  # Remove 'score' column temporarily
    df.insert(2, 'score', score_column)  # Insert 'score' column as the 3rd column

    # Sort DataFrame by 'score' in descending order
    df = df.sort_values(by='score', ascending=False)

    # Display the DataFrame
    print(df)

    # Save the DataFrame to a CSV file
    df.to_csv(f"{params['categories']}_{params['location']}_{params['term']}_yelp.csv", index=False)

    # Confirm save
    print(f"DataFrame saved as '{params['categories']}_{params['location']}_{params['term']}_yelp.csv'")

else:
    print("No businesses found in the response.")