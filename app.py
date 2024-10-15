import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import yfinance as yf
from prophet import Prophet
from statsmodels.tsa.seasonal import seasonal_decompose
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

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

def generate_buy_sell_signals(actual_data, forecast):
    signals = pd.DataFrame(index=actual_data.index)
    signals['price'] = actual_data['Close']
    signals['forecast'] = forecast['yhat'].values[:len(actual_data)]
    signals['signal'] = 0
    signals.loc[signals['price'] < signals['forecast'], 'signal'] = 1
    signals.loc[signals['price'] > signals['forecast'], 'signal'] = -1
    return signals

def plot_dashboard(actual_data, forecast, signals, decomposition, ticker):
    fig = make_subplots(rows=3, cols=1, subplot_titles=("Stock Price Prediction and Signals", "Buy/Sell Signals", "Time Series Decomposition"))
    
    # Plot actual and forecasted prices
    fig.add_trace(go.Scatter(x=actual_data['Date'], y=actual_data['Close'], name='Actual Price', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='Forecasted Price', line=dict(color='red', dash='dot')), row=1, col=1)
    
    # Plot buy/sell signals
    fig.add_trace(go.Scatter(x=signals.index, y=signals['signal'], name='Buy/Sell Signal', mode='markers',
                             marker=dict(size=8, color=signals['signal'], colorscale=[[0, 'red'], [0.5, 'yellow'], [1, 'green']], showscale=True)), row=2, col=1)
    
    # Plot time series decomposition
    fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend, name='Trend', line=dict(color='purple')), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, name='Seasonal', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid, name='Residual', line=dict(color='green')), row=3, col=1)
    
    fig.update_layout(height=1200, width=1000, title_text=f"{ticker} Trading Dashboard", template="plotly_dark")
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    
    return fig.to_json()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        return redirect(url_for('stock_dashboard', ticker=ticker))
    return render_template('index.html')

@app.route('/dashboard/<ticker>', methods=['GET'])
def stock_dashboard(ticker):
    return render_template('dashboard.html', ticker=ticker)

@app.route('/api/dashboard_data/<ticker>', methods=['GET'])
def dashboard_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)  # 5 years of historical data
    forecast_days = 30
    
    # Fetch stock data
    stock_data = fetch_stock_data(ticker, start_date, end_date)
    
    # Prepare data for Prophet
    prophet_data = prepare_data_for_prophet(stock_data)
    
    # Train Prophet model
    model = train_prophet_model(prophet_data)
    
    # Make future predictions
    forecast = make_future_predictions(model, forecast_days)
    
    # Generate buy/sell signals
    signals = generate_buy_sell_signals(stock_data, forecast)
    
    # Perform time series decomposition
    decomposition = seasonal_decompose(stock_data.set_index('Date')['Close'], model='additive', period=30)
    
    # Generate dashboard
    dashboard_json = plot_dashboard(stock_data, forecast, signals, decomposition, ticker)
    
    return jsonify({
        'dashboard': dashboard_json,
        'latest_price': stock_data['Close'].iloc[-1],
        'price_change': stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2],
        'forecast_price': forecast['yhat'].iloc[-1],
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
