#generated using automated tools 
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.graph_objs as go
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    stock_data = stock.history(start=start_date, end=end_date)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)
    return stock_data[['Date', 'Close']]

def train_model_and_forecast(data, forecast_days):
    model = ExponentialSmoothing(data['Close'], trend='add', seasonal='add', seasonal_periods=7)
    fit_model = model.fit()
    
    last_date = data['Date'].iloc[-1]
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_days)
    forecast = fit_model.forecast(forecast_days)
    forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': forecast})
    
    return forecast_df

def create_plot(actual_data, forecast_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual_data['Date'], y=actual_data['Close'], name='Actual Price'))
    fig.add_trace(go.Scatter(x=forecast_data['Date'], y=forecast_data['Forecast'], name='Forecasted Price'))
    fig.update_layout(title='Stock Price Prediction', xaxis_title='Date', yaxis_title='Price')
    return fig.to_html(full_html=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        start_date = '2020-01-01'
        end_date = datetime.now().strftime('%Y-%m-%d')
        forecast_days = 30

        try:
            stock_data = fetch_stock_data(ticker, start_date, end_date)
            forecast_data = train_model_and_forecast(stock_data, forecast_days)
            plot = create_plot(stock_data, forecast_data)
            return render_template('results.html', plot=plot, ticker=ticker)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('index.html', error=error_message)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)