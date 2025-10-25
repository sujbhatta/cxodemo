"""
Create sample stock data using only Python built-ins
"""

import random
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Seed for consistent data
random.seed(42)

# Data directory
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

# Stock configurations
STOCKS = {
    'RELIANCE.NS': {'base': 2850.00, 'vol': 30},
    'TCS.NS': {'base': 3650.00, 'vol': 40},
    'INFY.NS': {'base': 1450.00, 'vol': 20},
    'HDFCBANK.NS': {'base': 1650.00, 'vol': 25}
}

def generate_price_data(base_price, volatility, days=252):
    """Generate realistic price movements"""
    price = base_price
    data = []

    for i in range(days):
        # Random walk
        change_pct = random.uniform(-volatility, volatility) / base_price
        price = price * (1 + change_pct)

        # Generate OHLC
        open_price = price * random.uniform(0.995, 1.005)
        close_price = price
        high_price = max(open_price, close_price) * random.uniform(1.000, 1.010)
        low_price = min(open_price, close_price) * random.uniform(0.990, 1.000)
        volume = random.randint(4000000, 6000000)

        data.append({
            'Open': round(open_price, 2),
            'High': round(high_price, 2),
            'Low': round(low_price, 2),
            'Close': round(close_price, 2),
            'Volume': volume
        })

    return data

def generate_dates(days=252):
    """Generate trading dates (excluding weekends)"""
    dates = []
    current = datetime.now()
    count = 0

    while count < days:
        # Go backwards
        current = current - timedelta(days=1)
        # Skip weekends
        if current.weekday() < 5:  # Monday=0, Friday=4
            dates.append(current.strftime('%Y-%m-%d'))
            count += 1

    return list(reversed(dates))

print("Creating sample stock data for demo...")
print("=" * 60)

dates = generate_dates(252)

for symbol, config in STOCKS.items():
    print(f"\nCreating {symbol}...")

    price_data = generate_price_data(config['base'], config['vol'], 252)

    # Write CSV
    csv_path = DATA_DIR / f"{symbol}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

        for date, prices in zip(dates, price_data):
            writer.writerow([
                date,
                prices['Open'],
                prices['High'],
                prices['Low'],
                prices['Close'],
                prices['Volume']
            ])

    print(f"  ✓ Created {len(price_data)} rows")
    print(f"  Latest price: ₹{price_data[-1]['Close']:.2f}")
    print(f"  Saved to: {csv_path}")

print("\n" + "=" * 60)
print("✓ Sample data creation complete!")
print("\nDemo data ready for Hugging Face deployment! 🚀")
