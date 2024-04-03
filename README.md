# Best Restaurants Finder (with Google Maps API)

### The app is live here: https://best-restaurants-finder.streamlit.app/

# Background
- I had a personal problem and decided to solve it.
- In Yelp, you can only search for Top Rated or Most Reviewed restaurants. The problem with this is that the Most Reviewed restaurant may only be a 3.3 star place, and the Top Reviewed restaurant is usually a new or obscure place with 1 review by the owner.
- In Google Maps, we have the same issue. You are only allowed to search for a minimum Rating. No options to search by number of reviews.
- Therefore, since it appears that no one actually **uses** the product as a customer at both Yelp and Google Maps, I decided to try to implement this myself. A search engine for Restaurants (and other) based on 2 main criteria:
    1. A minimum number of reviews (eg. 500+ reviews), and
    2. a minimum rating (eg. 4.3+ stars)


# Jira To Do Nexts / Blockers

- Create master "score" that is some weighted combination of `n_rating` * `n_reviews`. Find some way to translate 4.1, 4.5, 4.7 into S, A, B, C, D, F tier.
- Drop down autofiller multiselect for city
- More exact error handling - what in the filter criteria caused the API to not be able to retrieve any data?
- Option to expand/reduce radius within City.
- Option to specify state so that the city is not confused with another state (eg. Paris, France vs. Paris, Texas) 
- Column for n miles away from current location.
- Given current location, permalink that gets directions to that place.
- Column for n minutes away including current traffic data from Google Maps.
- Any unstructured data (image of restaurant, embedded Google Maps snapshot)
- Column for current wait time at the restaurant.
- Column for make a reservation now (eg. with Resy)
- Non-urgent - current limitation is only 60 results from Google Maps API. Find a way to expand this past 60 results.

# Stack

- Python
- Google Maps API
- Streamlit
- Gumroad/Stripe (TBD)