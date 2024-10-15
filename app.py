import os
from flask import Flask, send_from_directory, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__, static_folder='.')

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    stock_data = stock.history(start=start_date, end=end_date)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)
    return stock_data[['Date', 'Close']]

def simple_forecast(data, forecast_days):
    X = np.arange(len(data)).reshape(-1, 1)
    y = data['Close'].values
    model = LinearRegression()
    model.fit(X, y)
    
    future_X = np.arange(len(data), len(data) + forecast_days).reshape(-1, 1)
    future_prices = model.predict(future_X)
    
    future_dates = pd.date_range(start=data['Date'].iloc[-1] + timedelta(days=1), periods=forecast_days)
    forecast = pd.DataFrame({'Date': future_dates, 'Close': future_prices})
    return forecast

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/dashboard_data/<ticker>')
def dashboard_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year of historical data
    forecast_days = 30
    
    # Fetch stock data
    stock_data = fetch_stock_data(ticker, start_date, end_date)
    
    # Simple forecast
    forecast = simple_forecast(stock_data, forecast_days)
    
    # Prepare data for frontend
    historical_data = stock_data['Close'].tolist()
    historical_dates = stock_data['Date'].dt.strftime('%Y-%m-%d').tolist()
    forecast_data = forecast['Close'].tolist()
    forecast_dates = forecast['Date'].dt.strftime('%Y-%m-%d').tolist()
    
    return jsonify({
        'historical_data': historical_data,
        'historical_dates': historical_dates,
        'forecast_data': forecast_data,
        'forecast_dates': forecast_dates,
        'latest_price': stock_data['Close'].iloc[-1],
        'price_change': stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2],
        'forecast_price': forecast['Close'].iloc[-1],
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
