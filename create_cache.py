"""
Script to pre-cache stock data for demo
Run this to fetch fresh data for all supported stocks
"""

import yfinance as yf
from pathlib import Path

# Stock symbols
STOCKS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys',
    'HDFCBANK.NS': 'HDFC Bank'
}

# Data directory
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

print("Fetching stock data for demo...")
print("=" * 60)

for symbol, name in STOCKS.items():
    print(f"\nFetching {name} ({symbol})...")
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period='1y', interval='1d')

        if df.empty:
            print(f"  ⚠ No data available for {symbol}")
            continue

        # Save to CSV
        cache_path = DATA_DIR / f"{symbol}.csv"
        df.to_csv(cache_path)
        print(f"  ✓ Saved {len(df)} rows to {cache_path}")
        print(f"  Latest price: ₹{df['Close'].iloc[-1]:.2f}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("✓ Cache creation complete!")
print(f"Files saved in: {DATA_DIR.absolute()}")
