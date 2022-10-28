import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="SME Default Prediction App",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_data():
    df = pd.read_csv('Technical_Task_Dataset.csv')
    return df

def load_model():
    model = pickle.load(open('classification.sav', 'rb'))
    return model

def plot_histogram(data, x, height, width, margin, title_text=None):
    fig = px.histogram(data, x=x)
    fig.update_layout(bargap=0.05, height=height, width=width, title_text=title_text, margin=dict(t=margin, b=margin))
    return fig

def plot_heatmap(corr, height, margin, title_text=None):
    fig = go.Figure(
        go.Heatmap(
        z=np.array(corr),
        x=corr.columns,
        y=corr.columns,
        colorscale=px.colors.diverging.RdBu,
        zmax=1,
        zmin=-1
        )
    )

#     cmap = sns.diverging_palette(230, 20, as_cmap=True)
#         fig = sns.heatmap(df6.corr(), mask=np.triu(np.ones_like(df6.corr(), dtype=bool)), 
#                           cmap=cmap, vmin=-1, vmax=1, center=0,
#                           square=True, linewidths=.5, cbar_kws={"shrink": .5})
        
    fig.update_layout(bargap=0.05, height=height, width=height+100, title_text=title_text, margin=dict(t=margin, b=margin))

    return fig
    
def prediction(model, c_exp, c_bank, ebitda, e_remun, profit, r_earn, t_asset, t_equity):
    prediction = model.predict([[c_exp, c_bank, ebitda, e_remun, profit, r_earn, t_asset, t_equity]])
    prediction_prob = model.predict_proba([[c_exp, c_bank, ebitda, e_remun, profit, r_earn, t_asset, t_equity]])
     
    if prediction == 'Default':
        pred = 'default'
        pred_prob = prediction_prob[0][0]*100
    else:
        pred = 'not default'
        pred_prob = prediction_prob[0][1]*100
    
    return pred, pred_prob


def main():
    """
    # SME Default Prediction App

    A machine learning app to predict the proability of a company's loan defaulting

    """    
      
    # ----------- Data -------------------
    
    df = load_data()
    model = load_model()
    
    
    # ----------- Sidebar ---------------
    
    condition = st.sidebar.selectbox("Select a page:",
                                     ("Introduction", "Data preprocessing", "The machine learning model", "Make a prediction"))
    
    # ------------- Introduction ------------------------
    
    if condition == 'Introduction':
        
        st.title("Loan Default Prediction App")
        st.write("A machine learning app to predict the proability of a SME's loan defaulting")
        
        st.subheader('About')

        st.write("""
        This app predicts the probability of a SME loan defaulting based on selected inputs. 
        The sidebar contains the following sections:
        - Exploratory data analysis
        - The machine learning model
        - Make a prediction
        """)
        
        st.subheader('Technical task questions')
        
        st.write("""
        1. In two or three paragraphs, please describe your methodological approach to the problem (e.g., how you framed the problem, any assumptions you made, why you chose certain techniques, etc). If applicable, please include any references to the literature that you used
            
            
        2. In 3 bullet points, please explain what feedback you'd give to the engineering team responsible for the data API to help them improve any aspect of the tool that you think would benefit
            - 1
            - 2
            - 3
        3. In 3 bullet points, please give guidance to the business regarding any suggestions you'd give them for using this model in production
            - 1
            - 2
            - 3
        4. What two things would you do to improve this test? One line for each.
            - 1
            - 2
        """)        
        
    # ------------- Data preprocessing ------------------------
    
    elif condition == 'Data preprocessing':
        
        st.title('Data preprocessing')
        
        st.subheader('Raw data')
        
        st.dataframe(df)
               
        st.subheader('Preprocessing steps')
        
        st.write("""
        Data was preprocessed using the following steps:
        - Remove rows which appear to have misentered data (e.g., negative numbers in the Account Year)
        - Set the data types
        - Subset where Account Year is equal to the year in Latest Accounts Date
        - Calculate the Years Since Incorporation (Account Year - Date of Incorporation)
        - Recode Trading Status to Default (previously Active) or Non-default (previously Dissolved or Liquidated/Receivership)
        - Fill NAs for the following using the equation in brackets:
            - Directors Remuneration (EBITDA + Directors Remuneration - EBITDA)
            - Total Assets (Total Current Assets + Total Non Current Assets)
            - Working Capital (Total Current Assets + Total Current Liabilities)
        - Drop Registered Number as it is unique for each company
        - Examine the correlation matrix and remove strongly correlated variables
        - Examine remaining features and drop those with a large portion of missing data or which are not adding value
        - Drop rows with NAs
        """)
        
        df2 = df[df.index.isin(df.query('1900 < `Account Year` < 2023').index)]
        df2=df2.convert_dtypes()
        df3 = df2.copy()
        for col in df3.columns:
            if df3[col].dtype == 'string':
                try:
                    df3[col] = pd.to_datetime(df2[col])
                except ValueError:
                    pass
        df4 = df3[df3['Latest Accounts Date'].dt.year==df3['Account Year']]
        df4['Years Since Incorporation'] = df4['Account Year']-df4['Date of Incorporation'].dt.year
        df4['Years Since Incorporation']= df4['Years Since Incorporation'].astype(int)
        df5 = df4.copy()
        df5['Trading Status'] = np.where(df5['Trading Status'] == 'Active', "Non-default", "Default")
        df5['Directors Remuneration'].fillna(df5['EBITDA + Directors Remuneration'] - df5['EBITDA'], inplace=True)
        df5['Total Assets'].fillna(df5['Total Current Assets'] + df5['Total Non Current Assets'], inplace=True)
        df5['Working Capital'].fillna(df5['Total Current Assets'] + df5['Total Current Liabilities'], inplace=True)        
        df6 = df5.drop(columns=['Registered Number','Account Year', 'Date of Incorporation', 'UK SIC Code',
                                'Bank Postcode', 'Registered or Trading Postcode', 'EBITDA + Directors Remuneration',
                                'Director Loans (current)', 'Director Loans (non-current)', 'Highest Paid Director ',
                                'Latest Accounts Date', 'Profit Before Tax + Directors Remuneration',
                                'EBIT', 'Highest Paid Director ', 'Total Non Current Liabilities (Incl Provisions)', 
                                'Wages', 'Working Capital', 'Leasehold', 'Bank Overdraft', 'Capital Expenditure'])
        df7 = df6.dropna(how='any').reset_index(drop=True)

        st.subheader('Correlation matrix')
        
        height, width, margin = 450, 1500, 10
        fig = plot_heatmap(corr=df5.corr(), height=700, margin=margin)

        st.plotly_chart(fig)
        
        st.write("""
        The correlation matrix shows some variables have strong correlations. 
        The following variables were removed as they are strongly correlated with one or more variable (> 0.90):
        - EBIT
        - Highest Paid Director
        - Total Non Current Liabilities (Incl Provisions)
        - Wages
        - Working Capital
        
        The following variables were removed:
        - Bank Overdraft
        - Bank Postcode
        - Capital Expenditure
        - Director Loans (current)
        - Director Loans (non-current)
        - EBITDA + Directors Remuneration
        - Latest Accounts Date
        - Leasehold
        - Profit Before Tax + Directors Remuneration
        - Registered or Trading Postcode
        - UK SIC Code
        """)
        
        st.subheader('Preprocessed data')
        
        st.dataframe(df7)
        
        st.subheader('Histogram of features')
        
        select_var = st.selectbox('Select a variable', [i for i in df6.columns])

        fig = plot_histogram(data=df7, x=select_var, height=height, width=width, margin=margin)

        st.plotly_chart(fig)
        
        
#         'Date of Incorporation', 'Latest Accounts Date', 'UK SIC Code',
#         'Account Year', 'Bank Postcode', 'Registered or Trading Postcode', 'EBITDA + Directors Remuneration',
#         'Director Loans (current)', 'Director Loans (non-current)', 'Highest Paid Director ',
#         'Profit Before Tax + Directors Remuneration'


        
        
    # ------------- The machine learning model ------------------------
    
    elif condition == 'The machine learning model':
        
        st.subheader('ML model')
    
    
    # ------------- Make a prediction ------------------------------
    
    elif condition == 'Make a prediction':
        
        st.subheader('Make a prediction')
        st.write("Enter the relevant fields below to predict the probability of a company's loan defaulty")
        
        # following lines create boxes in which user can enter data required to make prediction 
        c_exp = st.number_input('Capital expenditure')
        c_bank = st.number_input('Cash at the bank',0)
        ebitda = st.number_input('EBITDA')
        e_remun = st.number_input('Employees remuneration',0)
        profit = st.number_input('Profit for the year')
        r_earn = st.number_input('Retained earnings')
        t_asset = st.number_input('Total assets',0)
        t_equity = st.number_input('Total equity',0)
        result =""

        # when 'Predict' is clicked, make the prediction and store it 
        if st.button("Predict"): 
            res, res_prob = prediction(model, c_exp, c_bank, ebitda, e_remun, profit, r_earn, t_asset, t_equity) 
            st.success(f'This loan will {res} with a probability of {res_prob}%')


if __name__ == '__main__':
    main()
