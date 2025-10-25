"""
Generate realistic demo stock data for all 4 Indian stocks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Data directory
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# Stock configurations (approximate real values)
STOCKS = {
    'RELIANCE.NS': {'base_price': 2850, 'volatility': 0.015, 'trend': 0.0002},
    'TCS.NS': {'base_price': 3650, 'volatility': 0.012, 'trend': 0.0003},
    'INFY.NS': {'base_price': 1450, 'volatility': 0.013, 'trend': 0.0001},
    'HDFCBANK.NS': {'base_price': 1650, 'volatility': 0.014, 'trend': 0.0002}
}

def generate_stock_data(symbol, base_price, volatility, trend, days=252):
    """Generate realistic stock data"""

    # Generate dates (1 year of trading days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')[:days]  # B = business days

    # Generate prices with random walk
    np.random.seed(hash(symbol) % 2**32)  # Consistent random data per stock

    returns = np.random.normal(trend, volatility, days)
    price_series = base_price * (1 + returns).cumprod()

    # Generate OHLCV data
    data = []
    for i, date in enumerate(dates):
        close = price_series[i]
        open_price = close * (1 + np.random.normal(0, volatility/2))
        high = max(open_price, close) * (1 + abs(np.random.normal(0, volatility/3)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, volatility/3)))
        volume = int(np.random.lognormal(15, 0.5))  # Typical volume

        data.append({
            'Date': date,
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    return df

print("Generating demo stock data...")
print("=" * 60)

for symbol, config in STOCKS.items():
    print(f"\nGenerating {symbol}...")

    df = generate_stock_data(
        symbol,
        config['base_price'],
        config['volatility'],
        config['trend']
    )

    # Save to CSV
    cache_path = DATA_DIR / f"{symbol}.csv"
    df.to_csv(cache_path)

    print(f"  ✓ Generated {len(df)} rows")
    print(f"  Price range: ₹{df['Low'].min():.2f} - ₹{df['High'].max():.2f}")
    print(f"  Latest close: ₹{df['Close'].iloc[-1]:.2f}")
    print(f"  Saved to: {cache_path}")

print("\n" + "=" * 60)
print("✓ Demo data generation complete!")
print(f"\nFiles created in: {DATA_DIR.absolute()}")
print("\nThese CSV files will be used for the demo, ensuring:")
print("  ✓ Fast, reliable loading")
print("  ✓ No network dependencies")
print("  ✓ Consistent demo experience")
