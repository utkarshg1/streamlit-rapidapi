import requests
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import logging

# Load dotenv
load_dotenv()

# Get secrets
url = st.secrets["URL"]
api_key = st.secrets["API_KEY"]
host = st.secrets["HOST"]

# Ensure the logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Setup logging to save logs to a file
log_file = os.path.join(log_dir, "app.log")
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # To still see logs in the console
    ]
)

def symbol_search(company):
    try:
        logging.info(f"Searching for symbol: {company}")
        querystring = {"datatype": "json", "keywords": company, "function": "SYMBOL_SEARCH"}
        headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": host}
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(data["bestMatches"])
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        st.error("Failed to fetch symbol search data. Please try again.")
    except KeyError as e:
        logging.error(f"Unexpected response structure: {e}")
        st.error("Failed to parse the symbol search response. Please try again.")

def get_stock_daily(symbol):
    try:
        logging.info(f"Fetching daily stock data for symbol: {symbol}")
        querystring = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact", "datatype": "json"}
        headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": host}
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        st.error("Failed to fetch daily stock data. Please try again.")
    except KeyError as e:
        logging.error(f"Unexpected response structure: {e}")
        st.error("Failed to parse the daily stock data response. Please try again.")

def get_plotly_chart(df):
    try:
        logging.info("Generating plotly chart")
        fig = go.Figure(data=[
            go.Candlestick(
                x=df.index,
                open=df["1. open"],
                high=df["2. high"],
                low=df["3. low"],
                close=df["4. close"]
            )
        ])
        fig.update_layout(width=800, height=600)
        return fig
    except Exception as e:
        logging.error(f"Failed to generate chart: {e}")
        st.error("Failed to generate chart. Please try again.")

if __name__ == "__main__":
    st.set_page_config(page_title="Stock Market")
    st.title("Stock Market Details")

    # Create sidebar
    with st.sidebar:
        add_radio = st.radio(
            "Choose Endpoint",
            ("Symbol Search", "Daily Prices")
        )

    if add_radio == "Symbol Search":
        st.subheader("Symbol Search Endpoint")
        company = st.text_input("Please enter company name")
        if company:
            symbols = symbol_search(company)
            if symbols is not None:
                st.write("Response:")
                st.write(symbols)
    elif add_radio == "Daily Prices":
        st.subheader("Daily Prices")
        sym = st.text_input("Please enter symbol:")
        if sym:
            df = get_stock_daily(sym)
            if df is not None:
                st.write("Response:")
                st.write(df)
                fig = get_plotly_chart(df)
                if fig:
                    st.plotly_chart(fig)
