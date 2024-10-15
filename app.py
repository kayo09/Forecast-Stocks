from flask import Flask, jsonify, render_template, request
import pandas as pd
import yfinance as yf
from prophet import Prophet
from statsmodels.tsa.seasonal import seasonal_decompose
from datetime import datetime
import plotly.graph_objs as go
from plotly.subplots import make_subplots

app = Flask(__name__)

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    stock_data = stock.history(start=start_date, end=end_date)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)
    return stock_data[['Date', 'Close']]

def prepare_data_for_prophet(data):
    prophet_data = data.rename(columns={'Date': 'ds', 'Close': 'y'})
    return prophet_data

def train_prophet_model(data):
    model = Prophet(daily_seasonality=True)
    model.fit(data)
    return model

def make_future_predictions(model, periods):
    future_dates = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future_dates)
    return forecast

def generate_dashboard_plot(ticker):
    start_date = '2010-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    stock_data = fetch_stock_data(ticker, start_date, end_date)
    prophet_data = prepare_data_for_prophet(stock_data)
    model = train_prophet_model(prophet_data)
    forecast = make_future_predictions(model, 30)
    decomposition = seasonal_decompose(stock_data.set_index('Date')['Close'], model='additive', period=30)
    
    fig = make_subplots(rows=3, cols=1, subplot_titles=("Stock Price Prediction", "Buy/Sell Signals", "Time Series Decomposition"))
    fig.add_trace(go.Scatter(x=stock_data['Date'], y=stock_data['Close'], name='Actual Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecasted Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend, name='Trend'), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, name='Seasonal'), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid, name='Residual'), row=3, col=1)
    
    fig.update_layout(height=800, width=1000, title_text=f"{ticker} Trading Dashboard")
    return fig.to_json()

@app.route('/')
def home():
    return "<h1>Welcome to the Stock Dashboard</h1>"

@app.route('/dashboard/<ticker>')
def dashboard(ticker):
    graph_json = generate_dashboard_plot(ticker)
    return jsonify(graph_json)

if __name__ == "__main__":
    app.run(debug=True)

