################################
####### RISK MANAGEMENT ########
################################

import streamlit as st
import os
import datetime
import pandas as pd
import numpy as np

# Configurations & resources
from modules.gral_config import page_config, back_url_config
from modules.auth_config import auth_config

from modules.resources import post_meta_request, batch_post_request, single_post_request
from modules.data_processes import load_data, basic_trafo, today_filtering
from modules.gral_comp import title, total_metric, dataframe_with_selections
from modules.model_scoring import prediction_scores
from styles.basics import hide, lg_color, cont_padding

# Set page configuration and apply local styles
st.set_page_config(**page_config)
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True)
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True)
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

# HEADER IMAGE & TITLE
img = "images/DALLE-risk-management_cut.jpg"
st.image(img, use_container_width=True)
st.header("Risk Management")

### AUTHENTICATION
authenticator = auth_config()

try:
    authenticator.login('sidebar')
except Exception as e:
    st.error("Login failed: " + str(e))

if st.session_state.get('authentication_status'):
    welcome_col, ai_col = st.sidebar.columns((0.8, 0.2))
    with welcome_col:
        st.markdown(f"Welcome **{st.session_state.get('name')}**")
    with ai_col:
        if "ai" in st.session_state.get('roles'):
            st.markdown(":large_green_circle:", help="Full AI functions available")
            st.session_state.ai_powered = True
        else:
            st.markdown(":large_yellow_circle:", help="Basic AI functions available")
            st.session_state.ai_powered = False
    authenticator.logout('Logout', 'sidebar')
elif st.session_state.get('authentication_status') is False:
    st.sidebar.error('Username/password is incorrect')
    st.session_state.ai_powered = False
elif st.session_state.get('authentication_status') is None:
    st.sidebar.warning('Enter your username and password')
    st.session_state.ai_powered = False

# # INPUT: Date selector
# today = st.date_input(
#     "TODAY",
#     datetime.date(2014, 12, 24), # last day used for training
#     min_value=datetime.date(2014, 1, 1),
#     max_value=datetime.date(2014, 12, 24)
# )
today = datetime.date(2014, 12, 24)

################################
# DATA LOADING & PRE-PROCESSING
################################

# Load raw data and perform transformations
try:
    df_raw = load_data("data/import_data.csv")
    df_raw = basic_trafo(df_raw)
    df_today, df_pre_year, df_cur_year = today_filtering(df_raw, today)
except Exception as e:
    st.error("Error processing raw data: " + str(e))
    df_raw = pd.DataFrame()
    df_today, df_pre_year, df_cur_year = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load sample data for AI model
try:
    df_sample = load_data("data/sample_import_data.csv", index=0)
except Exception as e:
    st.error("Error loading sample data: " + str(e))
    df_sample = pd.DataFrame()

################################
# METADATA & MODEL INFORMATION
################################

risk_url = back_url_config["risk_url"]
# st.text(f"Risk URL: {risk_url}")
meta_endpoint = os.path.join(risk_url, 'metadata')


try:
    metadata = post_meta_request(meta_endpoint)
except Exception as e:
    st.error("Error retrieving metadata: " + str(e))

if metadata:
    try:
        # Create DataFrame and process metadata
        df_meta = pd.DataFrame(metadata, index=['metadata'])
        df_meta[['Hist rows', 'Hist columns']] = (
            df_meta['Hist data shape']
            .str.strip('()')
            .str.split(',', expand=True)
            .astype(str)
        )
        df_meta[['Dev rows', 'Dev columns']] = (
            df_meta['Dev data shape']
            .str.strip('()')
            .str.split(',', expand=True)
            .astype(str)
        )
        basic_meta_to_show = ['Model name', 'Model algorithm', 'Author',
                               'Optimal threshold', 'ROC AUC', 'F1 score']
        more_meta_to_show = ['Hist data start', 'Hist data end', 'Hist rows',
                             'Dev data start', 'Dev data end', 'Dev rows']
        new_names = {'ROC AUC': 'ROC AUC [%]',
                     'Optimal threshold': 'Optimal threshold [%]',
                     'F1 score': 'F1 score [%]'}
        percentage_columns = ['Optimal threshold', 'ROC AUC', 'F1 score']
        df_meta[percentage_columns] = df_meta[percentage_columns].astype(float) * 100
        df_meta['Optimal threshold'] = df_meta['Optimal threshold'].round(1)
        df_meta[percentage_columns] = df_meta[percentage_columns].astype(str)
        default_threshold = int(100 * float(metadata['Optimal threshold']))
    except Exception as e:
        st.error("Error processing metadata: " + str(e))
        default_threshold = 50  # fallback value
        df_meta = pd.DataFrame()
else:
    # st.error("No metadata available to display.")
    default_threshold = 50  # fallback value

################################
# BATCH PREDICTION FUNCTION (cached)
################################

@st.cache_data(show_spinner="Processing new sample for test")
def predict_batch(df_sample, batch_size, sample_size=None):
    # Remove column if exists
    try:
        df_sample.drop(columns=['formatted_date'], inplace=True)
    except Exception:
        pass

    if sample_size:
        df_sample = df_sample.sample(sample_size)

    num_batches = (len(df_sample) + batch_size - 1) // batch_size
    pred_results = pd.DataFrame()

    # Process each batch with error handling
    for i in range(num_batches):
        try:
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(df_sample))
            batch_data = df_sample.iloc[start_idx:end_idx].to_dict()
            batch_pred_result = batch_post_request(batch_data, os.path.join(risk_url, 'predict_batch'))
            batch_pred_result_df = pd.DataFrame(batch_pred_result)
            pred_results = pd.concat([pred_results, batch_pred_result_df], axis=0)
        except Exception as e:
            st.error(f"Error processing batch {i}: " + str(e))
            continue

    return df_sample, pred_results

################################
# TABS
################################

tabs = st.tabs(["Risk Management", "On-demand Risk", "Model Card"])
risk_tab, on_demand_tab, model_card_tab = tabs

################################
# RISK MANAGEMENT
with risk_tab:
    # Model general configuration
    st.subheader("Model test configuration")
    st.markdown("Configure the model and its assessment with new data")
    col_thr, col_sample, col_batch = st.columns((.5, .25, .25))

    with col_thr:
        st.session_state.threshold = 100 - st.slider(
            "Model sensibility %",
            value=100 - default_threshold,
            min_value=0,
            max_value=100,
            key="model_sensibility",
            help="How sensible is the AI model to the risk detected"
        )
    with col_sample:
        sample_size = st.number_input(
            "Sample size new",
            value=len(df_sample),
            min_value=100,
            max_value=len(df_sample),
            key="sample_size",
            help="Manage the total sample size sent to the model"
        )
    with col_batch:
        batch_size = st.number_input(
            "Batch size new",
            value=500,
            min_value=100,
            max_value=len(df_sample),
            key="batch_size",
            help="Manage the data batches sent to the model"
        )
    st.markdown("---")

    st.subheader("Metrics comparison")
    st.markdown("Compare the current RMS performance against the metrics got from the test")

    # Current metrics calculation
    col_curr, col_plusai = st.columns(2)

    with col_curr:
        st.markdown("Current metrics :female-detective:")
        
        col1, col2 = st.columns(2)
        with col1:
            try:
                items_ai = len(df_cur_year)
                items_df = len(df_pre_year)
                delta = (items_ai - items_df) / items_df
                st.metric(
                    label="CONTROLED ITEMS [PU]",
                    value="{:,.0f}".format(items_ai),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating controlled items: " + str(e))
        with col2:
            try:
                total_metric(df_pre_year, df_cur_year, 'illicit', 'ILLICITS', '', 'PU')
            except Exception as e:
                st.error("Error in total_metric for illicit: " + str(e))

        col1, col2 = st.columns(2)
        with col1:
            try:
                total_metric(df_pre_year, df_cur_year, 'RAISED_TAX_AMOUNT_USD', 'TAX RAISED', 'THOUSANDS', 'U$S')
            except Exception as e:
                st.error("Error in total_metric for tax raised: " + str(e))
        with col2:
            try:
                control_rate_df = 1.0  # since len(df_cur_year)/len(df_cur_year) is 1
                delta = 0.0
                st.metric(
                    label="CONTROL RATE [%]",
                    value="{:.0%}".format(control_rate_df),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating control rate: " + str(e))

        col1, col2 = st.columns(2)
        with col1:
            try:
                det_rate_df = df_cur_year['illicit'].sum() / len(df_cur_year)
                det_rate_pre = df_pre_year['illicit'].sum() / len(df_pre_year)
                delta = (det_rate_df - det_rate_pre) / det_rate_pre
                st.metric(
                    label="DETECTION RATE [%]",
                    value="{:.2%}".format(det_rate_df),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating detection rate: " + str(e))
        with col2:
            try:
                raise_rate_df = df_cur_year['RAISED_TAX_AMOUNT_USD'].sum() / df_cur_year['TOTAL.TAXES.USD'].sum()
                raise_rate_ai = df_pre_year['RAISED_TAX_AMOUNT_USD'].sum() / df_pre_year['TOTAL.TAXES.USD'].sum()
                delta = (raise_rate_df - raise_rate_ai) / raise_rate_ai
                st.metric(
                    label="TAX RAISED RATE [%]",
                    value="{:.2%}".format(raise_rate_df),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating tax raised rate: " + str(e))

    # New sample with AI testing
    try:
        df_sample, df_with_batch_pred_new = predict_batch(df_sample, batch_size=batch_size, sample_size=sample_size)
        df_with_batch_pred_new['prediction'] = np.where(
            df_with_batch_pred_new['proba'] >= st.session_state.threshold / 100, True, False
        )
        df_ai_controls_new = df_with_batch_pred_new[df_with_batch_pred_new['prediction']]
    except Exception as e:
        st.error("Error during batch prediction: " + str(e))
        df_ai_controls_new = pd.DataFrame()

    with col_plusai:
        st.markdown("#### New metrics + AI model :robot_face:")

        col1, col2 = st.columns(2)
        with col1:
            try:
                items_ai = len(df_ai_controls_new)
                items_df = len(df_sample)
                delta = (items_ai - items_df) / items_df
                st.metric(
                    label="CONTROLED ITEMS [PU]",
                    value="{:,.0f}".format(items_ai),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating AI controlled items: " + str(e))
        with col2:
            try:
                total_metric(df_sample, df_ai_controls_new, 'illicit', 'ILLICITS', '', 'PU')
            except Exception as e:
                st.error("Error in total_metric for AI illicit: " + str(e))

        col1, col2 = st.columns(2)
        with col1:
            try:
                total_metric(df_sample, df_ai_controls_new, 'RAISED_TAX_AMOUNT_USD', 'TAX RAISED', 'THOUSANDS', 'U$S')
            except Exception as e:
                st.error("Error in total_metric for AI tax raised: " + str(e))
        with col2:
            try:
                control_rate_ai = len(df_ai_controls_new) / len(df_sample)
                control_rate_df = 1.0
                delta = (control_rate_ai - control_rate_df) / control_rate_df
                st.metric(
                    label="CONTROL RATE [%]",
                    value="{:.0%}".format(control_rate_ai),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating AI control rate: " + str(e))

        col1, col2 = st.columns(2)
        with col1:
            try:
                det_rate_ai = df_ai_controls_new['illicit'].sum() / len(df_ai_controls_new)
                det_rate_df = df_sample['illicit'].sum() / len(df_sample)
                delta = (det_rate_ai - det_rate_df) / det_rate_df
                st.metric(
                    label="DETECTION RATE [%]",
                    value="{:.2%}".format(det_rate_ai),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating AI detection rate: " + str(e))
        with col2:
            try:
                raise_rate_ai = df_ai_controls_new['RAISED_TAX_AMOUNT_USD'].sum() / df_sample['TOTAL.TAXES.USD'].sum()
                raise_rate_df = df_sample['RAISED_TAX_AMOUNT_USD'].sum() / df_sample['TOTAL.TAXES.USD'].sum()
                delta = (raise_rate_ai - raise_rate_df) / raise_rate_df
                st.metric(
                    label="TAX RAISED RATE [%]",
                    value="{:.2%}".format(raise_rate_ai),
                    delta="{:.2%}".format(delta)
                )
            except Exception as e:
                st.error("Error calculating AI tax raised rate: " + str(e))

################################
# ON-DEMAND RISK
with on_demand_tab:
    st.subheader("On-demand tests")
    st.markdown("Use the risk model in new items, evaluating its on-demand capabilities")
    predict_endpoint = os.path.join(risk_url, 'predict')
    # Use a subset of the sample for inspection results
    ddt_result = df_sample[['illicit', 'RAISED_TAX_AMOUNT_USD']].astype(str)
    selection = dataframe_with_selections(df_sample)

    if st.button('Predict selection'):
        for index, row in selection.iterrows():
            try:
                data = df_sample.loc[index].to_dict()
                prediction_result = single_post_request(data, predict_endpoint)
            except Exception as e:
                st.error("Error predicting selection for index " + str(index) + ": " + str(e))
                continue

            results = {}
            try:
                results['Risk'] = 100 * float(prediction_result['proba'].strip("[]"))
                if results['Risk'] < st.session_state.threshold / 2:
                    results['Category'] = 'LOW 🟩'
                elif results['Risk'] < st.session_state.threshold:
                    results['Category'] = 'MEDIUM 🟧'
                else:
                    results['Category'] = 'HIGH 🟥'
                results.update(df_sample.loc[index].to_dict())
            except Exception as e:
                st.error("Error processing prediction result for index " + str(index) + ": " + str(e))
                continue

            st.text(f"Item {index} evaluation")
            pred_col, res_col = st.columns(2)
            with pred_col:
                st.text('IA Model output')
                try:
                    st.metric(label='Risk %', value=round(results['Risk'], 2))
                    st.metric(label='Category', value=results['Category'])
                except Exception as e:
                    st.error("Error displaying AI model output for index " + str(index) + ": " + str(e))
            with res_col:
                st.text('Inspection result')
                try:
                    st.write(ddt_result.loc[index].T)
                except Exception as e:
                    st.error("Error displaying inspection result for index " + str(index) + ": " + str(e))

            # Process explanation: compute feature importance and display top 5 positive and negative variables
            try:
                feature_importance = pd.DataFrame(prediction_result['expla'], index=['relevance']).T
                feature_importance['relevance'] = pd.to_numeric(feature_importance['relevance'])
                pos_importance = feature_importance.loc[feature_importance['relevance'] > 0].sort_values(by='relevance', ascending=False)
                pos_importance['%'] = round(100 * pos_importance['relevance'] / pos_importance['relevance'].sum(), 0)
                neg_importance = feature_importance.loc[feature_importance['relevance'] < 0].sort_values(by='relevance', ascending=True)
                neg_importance['relevance'] = -neg_importance['relevance']
                neg_importance['%'] = round(100 * neg_importance['relevance'] / neg_importance['relevance'].sum(), 0)
                pos_vars, neg_vars = st.columns(2)
                with pos_vars:
                    st.text('Risky variables ⚠️')
                    pos_top5 = pos_importance['%'].astype(str).head(5)
                    st.dataframe(pos_top5)
                with neg_vars:
                    st.text('Safe variables 👍')
                    neg_top5 = neg_importance['%'].astype(str).head(5)
                    st.dataframe(neg_top5)
            except Exception as e:
                st.error("Error processing feature importance for index " + str(index) + ": " + str(e))
            
            st.markdown("""---""")

################################
# MODEL CARD
with model_card_tab:
    if metadata:
        st.subheader("Model Card :robot_face:")
        st.markdown("Review the risk model metadata and its expected performance")
        col_card, col_data = st.columns(2)
        with col_card:
            try:
                st.markdown("General Metadata")
                st.write(df_meta[basic_meta_to_show].rename(columns=new_names).T)
            except Exception as e:
                st.error("Error displaying general metadata: " + str(e))
        with col_data:
            try:
                st.markdown("Development and Historical Data")
                st.write(df_meta[more_meta_to_show].T)
            except Exception as e:
                st.error("Error displaying historical data: " + str(e))

        st.write("Training Timestamp")
        col_time, _ = st.columns(2)
        with col_time:
            try:
                train_date, train_time = st.columns(2)
                with train_date:
                    st.write(df_meta['Training timestamp'].iloc[0].split('_')[0])
                with train_time:
                    st.write(df_meta['Training timestamp'].iloc[0].split('_')[1].replace('-', ':'))
            except Exception as e:
                st.error("Error displaying training timestamp: " + str(e))

        try:
            prediction_scores(df_with_batch_pred_new, 'illicit', 'prediction')
        except Exception as e:
            st.error("Error displaying prediction scores: " + str(e))
    else:
        st.error("No metadata available to display")

# Aiming to show errors and warnings in case that backend apps are down
