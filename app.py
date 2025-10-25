"""
Stock Research Dashboard
Flask backend with yfinance data, technical indicators, and Google Gemini AI reports
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from google import genai as vertex_genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle Google Cloud credentials for Hugging Face Spaces
# Spaces stores secrets as environment variables, but we need a JSON file
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
    import json
    creds_path = 'google_credentials.json'
    try:
        creds_data = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'))
        with open(creds_path, 'w') as f:
            json.dump(creds_data, f)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        print("✓ Created credentials file from environment variable")
    except Exception as e:
        print(f"⚠ Warning: Failed to create credentials from env var: {e}")

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

# Initialize Google Vertex AI Gemini client
gemini_client = None
if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    try:
        gemini_client = vertex_genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_PROJECT_ID', 'gemini-423216'),
            location=os.getenv('GOOGLE_LOCATION', 'us-central1')
        )
        print("✓ Gemini AI client initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Failed to initialize Gemini client: {e}")
else:
    print("⚠ Warning: GOOGLE_APPLICATION_CREDENTIALS not set")


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

    # Retry logic for network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Fetch 1 year of daily data
            stock = yf.Ticker(symbol)
            df = stock.history(period='1y', interval='1d', timeout=30)

            if df.empty:
                print(f"Attempt {attempt + 1}: No data returned for {symbol}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                raise ValueError(f"No data available for {symbol}. Please check the symbol or try again later.")

            # Save to cache
            df.to_csv(get_cache_path(symbol))
            print(f"✓ Cached {symbol} data ({len(df)} rows)")
            return df

        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} - Error fetching {symbol}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying...")
                time.sleep(2)
            else:
                raise Exception(f"Failed to fetch data for {symbol} after {max_retries} attempts. Error: {str(e)}")


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
    """Generate investment report using Google Gemini AI"""
    try:
        if not gemini_client:
            raise Exception("Gemini client not initialized. Please check your credentials.")

        # Prepare data summary for Gemini
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

        # Call Gemini API using Vertex AI client
        response = gemini_client.models.generate_content(
            model=os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp'),
            config=types.GenerateContentConfig(
                system_instruction="You are a professional financial analyst specializing in Indian stock markets and investment analysis.",
                temperature=0.3
            ),
            contents=prompt
        )

        report = response.text
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
    """API endpoint to generate investment report using Google Gemini"""
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
    # Get port from environment (for Hugging Face Spaces or other platforms)
    port = int(os.getenv('PORT', 7860))

    print("=" * 60)
    print("Starting Stock Research Dashboard...")
    print("=" * 60)
    print(f"Supported stocks: {', '.join(SUPPORTED_STOCKS.keys())}")
    print(f"Cache directory: {DATA_DIR.absolute()}")
    print(f"Cache TTL: {CACHE_TTL_HOURS} hours")
    print(f"Gemini Model: {os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')}")

    # Check for credentials
    if not gemini_client:
        print("\n⚠ WARNING: Gemini AI not configured!")
        print("Please set the following in your .env file:")
        print("  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/google.json")
        print("  - GOOGLE_PROJECT_ID=your-project-id")
        print("  - GOOGLE_LOCATION=us-central1")
        print("\nReport generation will not work until configured.")
    else:
        print("\n✓ Gemini AI configured and ready")

    print("=" * 60)
    print(f"\n🚀 Server starting on http://0.0.0.0:{port}\n")

    # Disable debug in production (Hugging Face Spaces)
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
