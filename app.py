from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
from prophet import Prophet
import plotly.graph_objs as go
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    stock_data = stock.history(start=start_date, end=end_date)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)
    return stock_data[['Date', 'Close']]

def prepare_data_for_prophet(data):
    return data.rename(columns={'Date': 'ds', 'Close': 'y'})

def train_prophet_model(data):
    model = Prophet(daily_seasonality=True)
    model.fit(data)
    return model

def make_future_predictions(model, periods):
    future_dates = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future_dates)
    return forecast

def create_plot(actual_data, forecast):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual_data['Date'], y=actual_data['Close'], name='Actual Price'))
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecasted Price'))
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
            prophet_data = prepare_data_for_prophet(stock_data)
            model = train_prophet_model(prophet_data)
            forecast = make_future_predictions(model, forecast_days)
            plot = create_plot(stock_data, forecast)
            return render_template('result.html', plot=plot)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('index.html', error=error_message)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)