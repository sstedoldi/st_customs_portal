################################
####### CLASSIFIER ########
################################

# app
import streamlit as st
# general
# import os
# import datetime
# import random
import time
import requests
# configutations
from modules.gral_config import page_config, back_url_config
# recourses

# processing
import pandas as pd
# import numpy as np
pd.options.display.float_format = '{:.2f}'.format
# # ploting
# import plotly.express as px
# import plotly.graph_objects as go
# local compenents
from modules.gral_comp import title
# local styles
from styles.basics import hide, lg_color, cont_padding

################################
################################
################################

### CONFIG
st.set_page_config(**page_config)

################################
################################
################################

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

################################
################################
################################

### HEADER
img = "images/DALLE-hs-classi_cut.jpg"
st.image(img, use_container_width=True)
st.header("HS Classification")

################################
################################
################################

### CONTENT

# FastAPI endpoint URL
clasi_url = back_url_config["clasi_url"]

################################
# TABS
################################

simple_clasi_tab, advanced_clasi_tab, clasi_analysis_tab, model_card_tab = st.tabs([
    "Simple Classification", "Advanced Classification", "Classification analysis", "Model Card"
])

################################
# SIMPLE CLASSI
with simple_clasi_tab:
    st.subheader("Simple Classification")
    st.markdown("Enter a product description to get predicted HS Codes with their legal texts")

    with st.form("simple_pred_form", border=False):
        description = st.text_input("Product Description", value="pure-bred breeding horses", key="simple_desc_input")
        topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1, key="simple_topn_input")
        submitted = st.form_submit_button("Predict HS Code")

    # Only run prediction if the form is submitted.
    if submitted:
        if description.strip():
            payload = {"description": description, "topn": topn}
            try:
                with st.spinner("Predicting HS Codes..."):
                    response = requests.post(f"{clasi_url}/predict_info", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    predictions = data.get("predictions", [])
                    if predictions:
                        for pred in predictions:
                            st.subheader(f"HS Code: {pred.get('predict')}")
                            st.write(f"**Score:** {pred.get('score')}")
                            hs_info = pred.get("hs_info", [])
                            if hs_info:
                                st.write("**HS Code Information:**")
                                st.write(f"{hs_info}")
                            st.markdown("---")
                    else:
                        st.info("No predictions were returned.")
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter a product description.")

################################
# ADVANCED CLASSI
with advanced_clasi_tab:
    st.subheader("Advanced Classification")
    st.markdown("Enter a product description to get predicted HS Codes and work with its tarif classification")

    with st.form("prediction_form", border=False):
        description = st.text_input("Product Description", value="pure-bred breeding horses", key="adv_desc_input")
        topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1, key="adv_topn_input")
        submitted = st.form_submit_button("Predict HS Code")

    # Only perform the prediction if the form is submitted and description is not empty.
    if submitted:
        if description.strip():
            payload = {"description": description, "topn": topn}
            try:
                with st.spinner("Predicting HS Codes..."):
                    response = requests.post(f"{clasi_url}/predict_info", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    predictions = data.get("predictions", [])
                    if predictions:
                        # Create a dictionary in session state to hold QA pairs.
                        if "qa_pairs" not in st.session_state:
                            st.session_state.qa_pairs = {}
                        
                        st.markdown("### Predictions and Related Questions")
                        # --- Form for Q&A (answers) and improving description ---
                        with st.form("qa_form", border=False):
                            # Iterate over each prediction
                            for pred in predictions:
                                hs_code = pred.get("predict")
                                score = pred.get("score")
                                hs_info = pred.get("hs_info", [])

                                st.markdown("---")
                                col_left, col_right = st.columns(2)
                                
                                with col_left:
                                    st.subheader(f"HS Code: {hs_code}")
                                    st.write(f"**Score:** {score}")
                                    if hs_info:
                                        st.write("**HS Code Information:**")
                                        if isinstance(hs_info, list):
                                            for info in hs_info:
                                                st.write(f"- {info}")
                                        else:
                                            st.write(hs_info)
                                
                                with col_right:
                                    st.markdown("**Questions Related**")
                                    question_payload = {"description": description, "hs06_code": hs_code}
                                    try:
                                        q_response = requests.post(f"{clasi_url}/questions_en_desc", json=question_payload)
                                        if q_response.status_code == 200:
                                            q_data = q_response.json()
                                            questions = q_data.get("questions", [])
                                            if questions:
                                                st.write("Please answer the following question(s):")
                                                # You can display the list of questions if needed.
                                                st.write(questions)
                                                # Each answer input is keyed with the hs_code.
                                                answer = st.text_input(f"Your Answer for HS Code {hs_code}", key=f"{hs_code}_q")
                                                st.session_state.qa_pairs[hs_code] = {"questions": questions, "answers": answer}
                                            else:
                                                st.info("No questions available for this HS Code.")
                                        else:
                                            st.error(f"Error getting questions for HS Code {hs_code}: {q_response.text}")
                                    except Exception as q_e:
                                        st.error(f"An error occurred while getting questions for HS Code {hs_code}: {q_e}")
                            
                            # Global submission button for the Q&A form.
                            improve_submitted = st.form_submit_button("Improve Description")
                        
                        # Process the improvement request only if the Q&A form was submitted.
                        if improve_submitted:
                            # Combine the QA pairs stored in session state
                            combined_qa_pairs = list(st.session_state.qa_pairs.values())
                            improve_payload = {"description": description, "qa_pairs": combined_qa_pairs}
                            try:
                                with st.spinner("Improving description..."):
                                    imp_response = requests.post(f"{clasi_url}/improve_en_desc", json=improve_payload)
                                if imp_response.status_code == 200:
                                    imp_data = imp_response.json()
                                    new_desc = imp_data.get("new_description", "")
                                    st.success("Enhanced Description:")
                                    st.write(new_desc)
                                else:
                                    st.error(f"Error {imp_response.status_code}: {imp_response.text}")
                            except Exception as imp_e:
                                st.error(f"An error occurred while improving description: {imp_e}")
                    else:
                        st.info("No predictions were returned.")
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter a product description.")

################################
# CLASSI ANALYSIS
with clasi_analysis_tab:
    st.subheader("Classification analysis")
    st.markdown("Improve the goods description using legal text and HS EN")

    st.markdown("---")
    st.markdown("Get a classification analysis using AI models")

################################


################################
# CLAS MODEL CARD
with model_card_tab:
    st.subheader("Model Card :robot_face:")
    st.markdown("Review the clasi model metadata and its expected performance")

################################
