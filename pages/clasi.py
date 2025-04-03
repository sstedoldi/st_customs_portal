################################
####### CLASSIFIER ########
################################

# app
import streamlit as st
# general
import re
import datetime
import requests
# import random
# import os
# configutations
from modules.gral_config import page_config, back_url_config
from modules.auth_config import auth_config

# recourses

# processing
import pandas as pd
# import numpy as np
pd.options.display.float_format = '{:.2f}'.format
# # ploting
# import plotly.express as px
import plotly.graph_objects as go
# local compenents
from modules.gral_comp import title, barplot_top_cat
# local styles
from styles.basics import hide, lg_color, cont_padding

################################
### CONFIG
################################
st.set_page_config(**page_config)

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

### HEADER
img = "images/DALLE-hs-classi_cut.jpg"
st.image(img, use_container_width=True)
st.header("HS Classification")

### AUTHENTICATION
authenticator = auth_config()

try:
    authenticator.login('sidebar')
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status'):
    welcome_col, ai_col = st.sidebar.columns((0.8,0.2))
    with welcome_col:
        st.markdown(f"Welcome **{st.session_state.get('name')}**")
    with ai_col:
        if "ai" in st.session_state.get('roles'):
            st.markdown(":large_green_circle:", help="Full AI functions available")
            st.session_state.ai_powered = True
        else:
            st.markdown(":large_yellow_circle:", help="Basic AI functions available")
            st.session_state.ai_powered = False
    authenticator.logout('Logout','sidebar')
elif st.session_state.get('authentication_status') is False:
    st.sidebar.error('Username/password is incorrect')
    st.session_state.ai_powered = False
elif st.session_state.get('authentication_status') is None:
    st.sidebar.warning('Enter your username and password')
    st.session_state.ai_powered = False

# FastAPI endpoint URL
clasi_url = back_url_config["clasi_url"]
st.write(f"CLASI URL: {clasi_url}")

################################
# TABS
################################

simple_clasi_tab, advanced_clasi_tab, clasi_analysis_tab, model_card_tab = st.tabs([
    "Simple Classification", "Description Improvement", "Classification analysis", "Model Card"
])

################################
# SIMPLE CLASSI
# Initialize simple classi session state variables
if "simple_predictions" not in st.session_state:
    st.session_state.simple_predictions = None
if "simple_candidate_hs_codes" not in st.session_state:
    st.session_state.simple_candidate_hs_codes = None
if "simple_description" not in st.session_state:
    st.session_state.simple_description = ""

with simple_clasi_tab:
    st.subheader("Simple Classification")
    st.markdown("Enter a product description to get predicted HS Codes with their legal texts")

    with st.form("simple_pred_form", border=False):
        description = st.text_input("Product Description", value="pure-bred breeding horses", key="simple_desc_input")
        topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1, key="simple_topn_input")
        submitted = st.form_submit_button("Predict :robot_face:", type="primary")

    # Only run prediction if the form is submitted.
    if submitted and description.strip():
        st.session_state.simple_description = description
        payload = {"description": description, "topn": topn}
        try:
            with st.spinner("Predicting HS Codes..."):
                response = requests.post(f"{clasi_url}/predict_info", json=payload)
            if response.status_code == 200:
                data = response.json()
                predictions = data.get("predictions", [])
                st.session_state.simple_predictions = predictions
            else:
                st.error(f"Error {response.status_code}: {response.text}") 
        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif submitted and not description.strip():
        st.warning("Please enter a product description.")
        
    # Display the predictions if available.
    if st.session_state.simple_predictions:
        st.markdown("#### Predictions")
        candidate_hs_codes = []
        for pred in st.session_state.simple_predictions:
            hs_code = pred.get("predict")
            candidate_hs_codes.append(hs_code)
            score = pred.get("score")
            hs_info = pred.get("hs_info", [])
            st.markdown(f"**HS Code:** {hs_code}  |  **Score:** {score}")
            if hs_info:
                st.write("**HS Code Information:**")
                st.write(f"{hs_info}")
            st.markdown("---")
        st.session_state.simple_candidate_hs_codes = candidate_hs_codes

################################
# ADVANCED CLASSI
# Initialize simple classi session state variables
if "adv_predictions" not in st.session_state:
    st.session_state.adv_predictions = None
if "adv_candidate_hs_codes" not in st.session_state:
    st.session_state.adv_candidate_hs_codes = None
if "adv_description" not in st.session_state:
    st.session_state.adv_description = ""
if "imp_description" not in st.session_state:
    st.session_state.imp_description = ""
if "answers_extention" not in st.session_state:
    st.session_state.answers_extention = 0
if "qa_pairs" not in st.session_state:
    st.session_state.qa_pairs = []

with advanced_clasi_tab:
    st.subheader("Description Improvement")
    st.markdown("Work out the goods description using AI generated questions coming from HS texts and EN")

    with st.form("adv_pred_form", clear_on_submit=False, border=False):
        description = st.text_input("Product Description", value="pure-bred breeding horses", key="adv_desc_input")
        topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1, key="adv_topn_input")
        submitted = st.form_submit_button("Process :robot_face:", type="primary", 
                                          disabled=not st.session_state.ai_powered)

    # If the prediction form is submitted and the description is not empty.
    if submitted and description.strip():
        st.session_state.adv_description = description
        payload = {"description": description, "topn": topn}
        try:
            with st.spinner("Predicting HS Codes..."):
                response = requests.post(f"{clasi_url}/predict_info", json=payload)
            if response.status_code == 200:
                data = response.json()
                predictions = data.get("predictions", [])
                st.session_state.adv_predictions = predictions 
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif submitted and not description.strip():
        st.warning("Please enter a product description.")

    # Only display the predictions section if predictions exist in session_state.
    if st.session_state.adv_predictions:
        prediction_col, questions_col = st.columns(2)

        with prediction_col:
            st.markdown("#### Predictions")
            candidate_hs_codes = []
            # Display the predictions.
            for pred in st.session_state.adv_predictions:
                hs_code = pred.get("predict")
                candidate_hs_codes.append(hs_code)
                score = pred.get("score")
                hs_info = pred.get("hs_info", [])
                st.markdown(f"**HS Code:** {hs_code}  |  **Score:** {score}")
                if hs_info:
                    st.write("**HS Code Information:**")
                    if isinstance(hs_info, list):
                        for info in hs_info:
                            st.write(f"- {info}")
                    else:
                        st.write(hs_info)
                st.markdown("---")
            # Save candidate HS codes for later use.
            st.session_state.adv_candidate_hs_codes = candidate_hs_codes

        with questions_col:
            # Only call questions endpoint if candidate HS codes are available.
            if st.session_state.adv_candidate_hs_codes:
                question_payload = {
                    "description": st.session_state.adv_description,
                    "top_hs06_codes": st.session_state.adv_candidate_hs_codes
                }
                try:
                    with st.spinner("Fetching questions for candidate HS Codes..."):
                        q_response = requests.post(f"{clasi_url}/questions_en_desc", json=question_payload)
                    if q_response.status_code == 200:
                        q_data = q_response.json()
                        questions = q_data.get("questions", [])
                        if questions:
                            st.markdown("#### Questions for Improving Description")
                            # Use a form to gather Q&A
                            with st.form("qa_form", clear_on_submit=False, border=False):
                                qa_pairs = []
                                answer_len = 0
                                for i, question in enumerate(questions):
                                    st.write(f"{i+1}. {question}")
                                    answer = st.text_input("Answer", key=f"answer_{i}", label_visibility="collapsed")
                                    answer_len += len(answer)
                                    qa_pairs.append({"question": question, "answer": answer})
                                improve_submitted = st.form_submit_button("Improve :sparkles:", type="primary", 
                                                    disabled=not st.session_state.ai_powered)
                        else:
                            st.info("No questions available for the candidate HS Codes.")
                    else:
                        st.error(f"Error fetching questions: {q_response.text}")
                except Exception as q_e:
                    st.error(f"An error occurred while fetching questions: {q_e}")

            # Process the improvement only if the Q&A form is submitted.
            if improve_submitted and answer_len > 6: # At least 6 characters as answers
                st.session_state.qa_pairs = qa_pairs
                st.session_state.answers_extention = answer_len
                improve_payload = {"description": st.session_state.adv_description, 
                                   "qa_pairs": st.session_state.qa_pairs}
                try:
                    with st.spinner("Improving description..."):
                        imp_response = requests.post(f"{clasi_url}/improve_en_desc", json=improve_payload)
                    if imp_response.status_code == 200:
                        imp_data = imp_response.json()
                        new_desc = imp_data.get("new_description", "")
                        st.success(new_desc)
                        match = re.search(r'"(.*)"', new_desc)
                        if match:
                            new_desc = match.group(1)
                        st.session_state.imp_description = new_desc
                    else:
                        st.error(f"Error {imp_response.status_code}: {imp_response.text}")
                except Exception as imp_e:
                    st.error(f"An error occurred while improving description: {imp_e}")
            elif improve_submitted and answer_len <= 6:
                st.warning("Please provide proper answers to the questions to improve the description.")

################################
# CLASSI ANALYSIS
# Initialize simple classi session state variables
if "clas_predictions" not in st.session_state:
    st.session_state.clas_predictions = None
if "clas_candidate_hs_codes" not in st.session_state:
    st.session_state.clas_candidate_hs_codes = None
if "clas_description" not in st.session_state:
    st.session_state.clas_description = ""
if "clas_report" not in st.session_state:
    st.session_state.clas_report = ""

def report_completion(description, topn, report):
    date_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    report_out = (
        f"#### Classification Report\n\n"
        f"{report}\n\n\n"
        f"*Date: {date_time}*\n\n"
        f"*Description provided: ''{description}''*\n\n"
        f"*Top N configured: {topn}*\n\n\n"
    )
    return report_out, date_time

with clasi_analysis_tab:
    st.subheader("Classification analysis")
    desc_col, load_col = st.columns((0.85, 0.15))
    with desc_col:  
        st.markdown("Get a classification report using an AI enhanced goods description")
    with load_col:
        load_desc = st.button("Load :arrow_down:", key="load_desc", type="secondary",
                            help="Load the improved description from the previous step", 
                            disabled=not st.session_state.imp_description,
                            use_container_width=True)
        if load_desc:
            st.session_state.clas_description = st.session_state.imp_description

    with st.form("clas_pred_form", clear_on_submit=False, border=False):
        if st.session_state.clas_description:
            description = st.text_input("Product Description :sparkles:", 
                                        value=st.session_state.clas_description, key="clas_desc_input")
        else:
            description = st.text_input("Product Description", value="pure-bred breeding horses", key="clas_desc_input")      
        topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1, key="clas_topn_input")
        submitted = st.form_submit_button("Analyse :robot_face:", type="primary",
                                          disabled=not st.session_state.ai_powered)
        
    # If the prediction form is submitted and the description is not empty.
    if submitted and description.strip():
        st.session_state.clas_description = description
        payload = {"description": st.session_state.clas_description, "topn": topn}
        try:
            with st.spinner("Analysing HS Classification..."):
                response = requests.post(f"{clasi_url}/classi_analysis", json=payload)
            if response.status_code == 200:
                data = response.json()
                report = data.get("report", "")
                st.session_state.clas_report = report
            else:
                st.error(f"Error {response.status_code}: {response.text}")
            if st.session_state.clas_report:
                st.session_state.clas_report, date_time = report_completion(st.session_state.clas_description,
                                            topn, st.session_state.clas_report)
                st.write(st.session_state.clas_report)
                doc_name = f"classification_report_{date_time}.txt"
                download = st.download_button("Save :floppy_disk:", st.session_state.clas_report, \
                                   doc_name, "text/plain")
            if download:
                st.write(st.session_state.clas_report)
                st.success(f"Report saved as {doc_name}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif submitted and not description.strip():
        st.warning("Please enter a product description.")

################################
# CLAS MODEL CARD
# Initialize simple classi session state variables
if "metadata" not in st.session_state:
    st.session_state.metadata = None

with model_card_tab:
    st.subheader("Model Card :robot_face:")
    st.markdown("Review the clasi model metadata and its expected performance")
 
    try:
        with st.spinner("Getting model metadata..."):
            response = requests.post(f"{clasi_url}/metadata")
        if response.status_code == 200:
            metadata = response.json()
            st.session_state.metadata = metadata.get("metadata", None)
        else:
            st.error(f"Error {response.status_code}: {response.text}")

        if st.session_state.metadata:
            metadata = st.session_state.metadata

            # Basic Information and Performance Metrics
            basic_col, metrics_col = st.columns(2)

            # Basic Model Information
            with basic_col:
                st.markdown("General Metadata")
                gral_metadata = [
                    ["Model name", metadata.get("model_name",None)],
                    ["Model library", metadata.get("model_lib",None)],
                    ["Model author", metadata.get("model_author",None)],
                    ["Embedding Dim", metadata.get("embedding_dimension", None)],
                    ["Epochs", metadata.get("epochs", None)],
                ]
                df_basic = pd.DataFrame(gral_metadata, columns=["Parameter", "Value"]).astype(str)
                df_basic.set_index("Parameter", drop=True, inplace=True)
                st.table(df_basic)

            # Model Performance Metrics
            with metrics_col:
                st.markdown("Performance Metrics")
                eval_metrics = metadata.get("evaluation", {})
                overall_accuracy = float(eval_metrics.get("overall_accuracy", None)) * 100
                ci = eval_metrics.get("accuracy_confidence_interval", {})
                basic_perf = [
                    ["Overall Accuracy", overall_accuracy],
                    ["Confidence Mean", float(ci.get("mean", None)) * 100],
                    ["Lower Bound", round(float(ci.get("lower_bound", None)),3) * 100],
                    ["Upper Bound", round(float(ci.get("upper_bound", None)),3) * 100],
                ]
                df_perf = pd.DataFrame(basic_perf, columns=["Metric", "Value"]).astype(str)
                df_perf.set_index("Metric", drop=True, inplace=True)
                st.table(df_perf)

            # Training Timestamp & Samples
            time_col, samples_col = st.columns(2)
            with time_col:
                st.write("Training Timestamp")
                train_date, train_time = st.columns(2)
                with train_date:
                    st.write(metadata["training"].get("training_date", None).split("_")[0])
                with train_time:
                    st.write(metadata["training"].get("training_date", None).split("_")[1].replace('-', ':'))
            with samples_col:
                st.write("Training Samples")
                st.write(str(metadata["training"].get("train_samples", None)))

            st.markdown("---")
            st.markdown("Aggregated Test Performance by HS Chapters")

            hs_metrics = eval_metrics.get("hs_code_metrics", {})

            # Aggregated performance by HS Chapter (first 2 digits)
            hs06_test = pd.DataFrame(hs_metrics).T
            hs06_test["chapter"] = hs06_test.index.str[:2]

            # Build a DataFrame that contains chapter-level totals.
            chapters_set = set()
            for code, metrics in hs_metrics.items():
                chapter = code[:2]
                chapters_set.add(chapter)
            
            total_samples = []
            correct_pred = []
            for chapter in chapters_set:
                df_chapter = hs06_test[hs06_test["chapter"] == chapter]
                if len(df_chapter) > 0:
                    total_samples.append(df_chapter["total_samples"].sum())
                    correct_pred.append(df_chapter["correct_predictions"].sum())
                else:
                    total_samples.append(0)
                    correct_pred.append(0)
            
            hs02_test = pd.DataFrame({
                "chapter": list(chapters_set),
                "total_samples": total_samples,
                "correct_predictions": correct_pred
            })
            hs02_test["accuracy"] = hs02_test["correct_predictions"]/hs02_test["total_samples"]
            hs02_test.sort_values('total_samples', ascending=False, inplace=True)

            top_col, bot_col = st.columns(2)
            with top_col:
                barplot_top_cat(hs02_test, "chapter", "total_samples", top_n=None, 
                                title="HS Chapters by Total Samples")
            with bot_col:
                barplot_top_cat(hs02_test, "chapter", "accuracy", top_n=None, 
                                title="HS Chapters by Accuracy")

    except Exception as e:
        st.error(f"An error occurred: {e}")


################################
