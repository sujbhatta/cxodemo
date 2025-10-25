"""
Stock Research Dashboard
Flask backend with yfinance data, technical indicators, and Claude AI reports
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configuration
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
CACHE_TTL_HOURS = 24
SUPPORTED_STOCKS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys',
    'HDFCBANK.NS': 'HDFC Bank'
}

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


def get_cache_path(symbol):
    """Get the cache file path for a stock symbol"""
    return DATA_DIR / f"{symbol}.csv"


def is_cache_valid(symbol):
    """Check if cached data exists and is within TTL"""
    cache_path = get_cache_path(symbol)
    if not cache_path.exists():
        return False

    # Check file modification time
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime
    return age < timedelta(hours=CACHE_TTL_HOURS)


def fetch_stock_data(symbol):
    """Fetch stock data from yfinance or cache"""
    # Check cache first
    if is_cache_valid(symbol):
        print(f"Loading {symbol} from cache")
        df = pd.read_csv(get_cache_path(symbol), index_col=0, parse_dates=True)
        return df

    print(f"Fetching {symbol} from yfinance")
    try:
        # Fetch 1 year of daily data
        stock = yf.Ticker(symbol)
        df = stock.history(period='1y', interval='1d')

        if df.empty:
            raise ValueError(f"No data returned for {symbol}")

        # Save to cache
        df.to_csv(get_cache_path(symbol))
        print(f"Cached {symbol} data ({len(df)} rows)")
        return df

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        raise


def calculate_moving_averages(df):
    """Calculate 20, 50, and 200-day moving averages"""
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    return df


def calculate_rsi(df, period=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    df['RSI'] = rsi
    return df


def get_stock_metadata(symbol):
    """Get additional stock metadata"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        return {
            'name': SUPPORTED_STOCKS.get(symbol, symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            '52w_high': info.get('fiftyTwoWeekHigh', 0),
            '52w_low': info.get('fiftyTwoWeekLow', 0),
        }
    except Exception as e:
        print(f"Error fetching metadata for {symbol}: {e}")
        return {
            'name': SUPPORTED_STOCKS.get(symbol, symbol),
            'sector': 'N/A',
            'industry': 'N/A',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            '52w_high': 0,
            '52w_low': 0,
        }


def generate_investment_report(symbol, stock_data, metadata):
    """Generate investment report using Claude AI"""
    try:
        # Prepare data summary for Claude
        latest = stock_data.iloc[-1]
        prev = stock_data.iloc[-2]

        # Price change
        price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

        # 52-week performance
        year_high = stock_data['Close'].max()
        year_low = stock_data['Close'].min()
        current_vs_high = ((latest['Close'] - year_high) / year_high) * 100

        # Moving average signals
        ma_signals = []
        if latest['Close'] > latest['MA20']:
            ma_signals.append("above 20-day MA (bullish short-term)")
        else:
            ma_signals.append("below 20-day MA (bearish short-term)")

        if latest['Close'] > latest['MA50']:
            ma_signals.append("above 50-day MA (bullish medium-term)")
        else:
            ma_signals.append("below 50-day MA (bearish medium-term)")

        # RSI signal
        rsi_value = latest['RSI']
        if rsi_value > 70:
            rsi_signal = "overbought (RSI > 70)"
        elif rsi_value < 30:
            rsi_signal = "oversold (RSI < 30)"
        else:
            rsi_signal = f"neutral (RSI = {rsi_value:.1f})"

        prompt = f"""You are a professional financial analyst. Write a concise investment research report for {metadata['name']} ({symbol}).

Current Data:
- Current Price: ₹{latest['Close']:.2f} ({price_change:+.2f}% from yesterday)
- 52-Week High: ₹{year_high:.2f} (currently {current_vs_high:+.1f}% from high)
- 52-Week Low: ₹{year_low:.2f}
- P/E Ratio: {metadata['pe_ratio']:.2f}
- Market Cap: ₹{metadata['market_cap']:,.0f}
- Sector: {metadata['sector']}

Technical Indicators:
- Price is {', '.join(ma_signals)}
- RSI indicator shows {rsi_signal}

Write a 200-300 word report with:
1. Investment Thesis (2-3 sentences on why to invest/avoid)
2. Key Risks (2-3 bullet points)
3. Recommendation (Buy/Hold/Sell with rationale)

Keep it professional, data-driven, and executive-friendly. Focus on facts, not speculation."""

        # Call Claude API
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        report = message.content[0].text
        return {
            'success': True,
            'report': report,
            'generated_at': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error generating report: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html', stocks=SUPPORTED_STOCKS)


@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """API endpoint to get stock data with technical indicators"""
    try:
        if symbol not in SUPPORTED_STOCKS:
            return jsonify({'error': f'Unsupported stock symbol: {symbol}'}), 400

        # Fetch stock data
        df = fetch_stock_data(symbol)

        # Calculate indicators
        df = calculate_moving_averages(df)
        df = calculate_rsi(df)

        # Get metadata
        metadata = get_stock_metadata(symbol)

        # Prepare response
        # Convert DataFrame to list of dicts for JSON
        df_reset = df.reset_index()
        df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')

        # Replace NaN with None for JSON serialization
        df_reset = df_reset.replace({np.nan: None})

        data = {
            'symbol': symbol,
            'name': metadata['name'],
            'metadata': metadata,
            'current_price': float(df['Close'].iloc[-1]),
            'price_data': df_reset.to_dict('records'),
            'cache_status': 'cached' if is_cache_valid(symbol) else 'fresh'
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/<symbol>')
def get_investment_report(symbol):
    """API endpoint to generate investment report using Claude"""
    try:
        if symbol not in SUPPORTED_STOCKS:
            return jsonify({'error': f'Unsupported stock symbol: {symbol}'}), 400

        # Fetch stock data
        df = fetch_stock_data(symbol)
        df = calculate_moving_averages(df)
        df = calculate_rsi(df)

        # Get metadata
        metadata = get_stock_metadata(symbol)

        # Generate report
        report_data = generate_investment_report(symbol, df, metadata)

        return jsonify(report_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks')
def get_available_stocks():
    """API endpoint to get list of supported stocks"""
    return jsonify({
        'stocks': [
            {'symbol': symbol, 'name': name}
            for symbol, name in SUPPORTED_STOCKS.items()
        ]
    })


if __name__ == '__main__':
    print("Starting Stock Research Dashboard...")
    print(f"Supported stocks: {', '.join(SUPPORTED_STOCKS.keys())}")
    print(f"Cache directory: {DATA_DIR.absolute()}")
    print(f"Cache TTL: {CACHE_TTL_HOURS} hours")

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("WARNING: ANTHROPIC_API_KEY not set. Report generation will fail.")
        print("Please create a .env file with your API key.")

    app.run(debug=True, host='0.0.0.0', port=5000)
