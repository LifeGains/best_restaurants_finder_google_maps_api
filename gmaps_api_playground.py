import inspect
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
from pprint import pprint

pd.set_option('display.float_format', lambda x: '%.2f' % x)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


# Path
dotenv_path = 'C:\\Users\\kevin\\Google Drive\\My Drive\\Github\\all-api-keys\\.env'
load_dotenv(dotenv_path)

# Load api key
gmaps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(gmaps_api_key)

# Get the signature of the function
sig = inspect.signature(gmaps.places)

# Print the parameters of the function
print(sig.parameters)