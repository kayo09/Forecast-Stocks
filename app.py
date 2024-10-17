# app.py
from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import json

app = Flask(__name__)

def fetch_stock_data(ticker, start_date, end_date):
    try:
        stock = yf.Ticker(ticker)
        stock_data = stock.history(start=start_date, end=end_date)
        stock_data.reset_index(inplace=True)
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)
        return stock_data[['Date', 'Close']]
    except Exception as e:
        raise ValueError(f"Error fetching data for {ticker}: {str(e)}")

def train_model_and_forecast(data, forecast_days):
    try:
        model = ARIMA(data['Close'], order=(1, 1, 1))
        fit_model = model.fit()
        
        last_date = data['Date'].iloc[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days)
        forecast = fit_model.forecast(steps=forecast_days)
        forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': forecast})
        
        return forecast_df
    except Exception as e:
        raise ValueError(f"Error in model training and forecasting: {str(e)}")

def create_plot_data(actual_data, forecast_data):
    actual_trace = go.Scatter(x=actual_data['Date'], y=actual_data['Close'], name='Actual Price', line=dict(color='#4299E1'))
    forecast_trace = go.Scatter(x=forecast_data['Date'], y=forecast_data['Forecast'], name='Forecasted Price', line=dict(color='#F56565'))
    
    layout = go.Layout(
        title='Stock Price Prediction',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Price'),
        template='plotly_dark',
        height=500
    )
    
    return {'data': [actual_trace, forecast_trace], 'layout': layout}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker'].upper()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        forecast_days = 30
        
        try:
            stock_data = fetch_stock_data(ticker, start_date, end_date)
            forecast_data = train_model_and_forecast(stock_data, forecast_days)
            plot_data = create_plot_data(stock_data, forecast_data)
            
            current_price = stock_data['Close'].iloc[-1]
            forecast_price = forecast_data['Forecast'].iloc[-1]
            price_diff = forecast_price - current_price
            trend_percentage = (price_diff / current_price) * 100

            response_data = {
                'success': True,
                'plot': json.loads(json.dumps(plot_data, cls=PlotlyJSONEncoder)),
                'current_price': round(current_price, 2),
                'forecast_price': round(forecast_price, 2),
                'trend_percentage': round(trend_percentage, 2)
            }
            
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)