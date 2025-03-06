import streamlit as st
import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
import matplotlib.pyplot as plt
import seaborn as sns

# Load your data
def prediction_scores(data, real_col, pred_col):
    # Calculate metrics
    true_positive = ((data[real_col] == True) & (data[pred_col] == True)).sum()
    false_positive = ((data[real_col] == False) & (data[pred_col] == True)).sum()
    false_negative = ((data[real_col] == True) & (data[pred_col] == False)).sum()
    true_negative = ((data[real_col] == False) & (data[pred_col] == False)).sum()

    accuracy = (true_positive + true_negative) / len(data)
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) != 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) != 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0

    col1, col2= st.columns((0.5,0.5))

    scores = pd.DataFrame({
        'Accuracy' : [100*accuracy],
        'Precision' : [100*precision],
        'Recall' : [100*recall],
        'F1 score' : [100*f1],
    },
    index=['Scores [%]'])

    # Display metrics
    with col1:
        st.write("Sample shape: ", data.shape)
        st.dataframe(scores.T)
        show_formulas = st.checkbox("See formulas", value=False)

    # Calculate confusion matrix manually
    conf_matrix = pd.DataFrame(
        {
            'Predicted Fraud': [true_positive, false_positive],
            'Predicted Legal': [false_negative, true_negative]
        },
        index=['Real Fraud', 'Real Legal']
    )
    with col2:
        # Create confusion matrix plot
        st.write("Confusion Matrix")
        fig, ax = plt.subplots()
        sns.heatmap(conf_matrix, annot=True, fmt='d', cbar=False, ax=ax)#, cmap='plasma')
        st.pyplot(fig)
    
    if show_formulas:
        col1, col2 = st.columns(2)
        with col1:
            st.latex(r"Accuracy: \frac{TP+TN}{TP+TN+FP+FN}", help="General score")
            st.latex(r"Precision: \frac{TP}{TP+FP}", help="Non-productive control score")
        with col2:
            st.latex(r"Recall: \frac{TP}{TP+FN}", help="Non-detected fraud score")
            st.latex(r"F1: \frac{2*Pre*Rec}{Pre+Rec}", help="Harmonic mean of Precision and Recall")
        # help='''
        # TP: Predicted Fraud and Real Fraud,
        # TN: Predicted Legitimate and Real Legitimate,
        # FP: Predicted Fraud and Real Legitimate,
        # FN: Predicted Legitimate and Real Fraud.
        # '''