import streamlit as st
import numpy as np
import pandas as pd
import requests

# model metadata
@st.cache_resource
def post_meta_request(endpoint):
    print("requesting model metadata")
    try:
        response = requests.post(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}
    
# batch processing
@st.cache_resource
def batch_post_request(data, endpoint):
    print("requesting batch prediction")
    try:
        response = requests.post(endpoint, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}
    
# single processing
@st.cache_resource
def single_post_request(data, endpoint):
    print("requesting single prediction")
    try:
         # Replace infinite and NaN values with None
        data = {key: None if pd.isna(value) or value in [np.inf, -np.inf] else value for key, value in data.items()}

        response = requests.post(endpoint, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Server Error'}
    except Exception as e:
        print(e)
        return {'error': 'Connection Error'}