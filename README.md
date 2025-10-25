# Stock Research Dashboard

A production-ready stock analysis dashboard powered by Flask, yfinance, and Claude AI. This application provides real-time technical analysis and AI-generated investment reports for Indian stocks.

![Dashboard Preview](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![Claude AI](https://img.shields.io/badge/Claude-Sonnet%204.5-purple)

## Features

### Core Capabilities
- **Real-time Stock Data**: Fetch 1 year of daily OHLCV data for Indian stocks
- **Technical Analysis**: Automated calculation of 20/50/200-day Moving Averages and RSI(14)
- **AI-Powered Reports**: Claude Sonnet 4.5 generates professional investment analysis
- **Smart Caching**: Filesystem-based caching with 24-hour TTL for optimal performance
- **Modern UI**: Clean, responsive Bootstrap 5 interface with Chart.js visualizations

### Supported Stocks
- **RELIANCE** (Reliance Industries)
- **TCS** (Tata Consultancy Services)
- **INFY** (Infosys)
- **HDFC** (HDFC Bank)

## Project Structure

```
cxodemo/
├── app.py                  # Flask backend with API endpoints
├── templates/
│   └── index.html         # Bootstrap frontend with Chart.js
├── data/                  # Cached stock data (CSV files)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
└── README.md             # This file
```

## Technical Stack

### Backend
- **Flask 3.0**: Web framework
- **yfinance**: Yahoo Finance API client for stock data
- **pandas + numpy**: Data processing and technical indicators
- **Anthropic Claude API**: AI-powered report generation

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Chart.js 4.4**: Interactive price and RSI charts
- **Vanilla JavaScript**: No framework dependencies

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd cxodemo
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

5. **Create data directory** (if not exists)
   ```bash
   mkdir -p data
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Production Mode

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Usage Guide

### 1. Select a Stock
- Open the dashboard in your browser
- Use the dropdown to select one of the 4 supported stocks
- Data will load automatically

### 2. View Technical Analysis
- **Price Chart**: Shows closing prices with 20/50/200-day moving averages
- **RSI Chart**: Displays Relative Strength Index (oversold < 30, overbought > 70)
- **Key Metrics**: View 52-week high/low, P/E ratio, market cap, and sector

### 3. Generate AI Report
- Click "Generate Report" button
- Claude AI will analyze the stock and provide:
  - Investment thesis (2-3 sentences)
  - Key risks (bullet points)
  - Recommendation (Buy/Hold/Sell with rationale)
- Reports are 200-300 words, professional and data-driven

## API Endpoints

### GET `/api/stocks`
Returns list of supported stocks
```json
{
  "stocks": [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries"},
    ...
  ]
}
```

### GET `/api/stock/<symbol>`
Returns complete stock data with technical indicators
```json
{
  "symbol": "RELIANCE.NS",
  "name": "Reliance Industries",
  "current_price": 2845.50,
  "metadata": {
    "52w_high": 2968.00,
    "52w_low": 2220.30,
    "pe_ratio": 28.45,
    "market_cap": 19234567890000,
    "sector": "Energy"
  },
  "price_data": [
    {
      "Date": "2024-01-01",
      "Open": 2800.00,
      "High": 2825.00,
      "Low": 2795.00,
      "Close": 2820.00,
      "Volume": 5234567,
      "MA20": 2810.50,
      "MA50": 2795.30,
      "MA200": 2650.80,
      "RSI": 62.45
    },
    ...
  ],
  "cache_status": "cached"
}
```

### GET `/api/report/<symbol>`
Generates AI investment report
```json
{
  "success": true,
  "report": "Investment Thesis: ...",
  "generated_at": "2024-10-25T15:30:00"
}
```

## Caching Strategy

- **Location**: Filesystem (`data/` directory)
- **Format**: CSV files named `{SYMBOL}.csv`
- **TTL**: 24 hours (configurable via `CACHE_TTL_HOURS`)
- **Behavior**:
  - First request fetches from yfinance and caches
  - Subsequent requests use cached data
  - Cache refreshes automatically after TTL expires
- **Offline Mode**: Works with cached data after initial fetch

## Technical Indicators

### Moving Averages (MA)
- **MA20**: 20-day moving average (short-term trend)
- **MA50**: 50-day moving average (medium-term trend)
- **MA200**: 200-day moving average (long-term trend)

**Signal Interpretation**:
- Price > MA: Bullish signal
- Price < MA: Bearish signal
- Golden Cross (MA50 > MA200): Strong buy signal
- Death Cross (MA50 < MA200): Strong sell signal

### Relative Strength Index (RSI)
- **Period**: 14 days
- **Range**: 0-100
- **Interpretation**:
  - RSI > 70: Overbought (potential sell signal)
  - RSI < 30: Oversold (potential buy signal)
  - RSI 30-70: Neutral zone

## Error Handling

The application includes production-ready error handling:
- Network errors (yfinance API failures)
- Invalid stock symbols
- Missing API keys
- Cache corruption
- Claude API errors

All errors are logged to console and displayed to users with helpful messages.

## Development Notes

### Adding More Stocks
Edit `SUPPORTED_STOCKS` dictionary in `app.py`:
```python
SUPPORTED_STOCKS = {
    'SYMBOL.NS': 'Company Name',
    ...
}
```

### Customizing Cache TTL
Modify `CACHE_TTL_HOURS` in `app.py`:
```python
CACHE_TTL_HOURS = 24  # Change to desired hours
```

### Customizing Report Length
Edit the prompt in `generate_investment_report()` function:
```python
prompt = f"""..."""  # Modify instructions
```

## Demo Instructions

### For CEO Presentations
1. Start the application
2. Select RELIANCE (widely known stock)
3. Show the price chart with MAs
4. Explain RSI indicator
5. Generate AI report and discuss insights
6. Highlight key features:
   - Real-time data with smart caching
   - Professional technical analysis
   - AI-powered investment research
   - Production-ready architecture

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"
**Solution**: Create `.env` file with your API key

### Issue: "Failed to fetch stock data"
**Solution**: Check internet connection and verify stock symbols

### Issue: Charts not displaying
**Solution**: Check browser console for JavaScript errors, ensure Chart.js CDN is accessible

### Issue: Old data showing
**Solution**: Delete cache files in `data/` directory to force refresh

## Future Enhancements (v2)

- [ ] Export reports to PDF
- [ ] Email alerts for price changes
- [ ] Portfolio tracking
- [ ] More stocks (NSE Top 50)
- [ ] Comparison view (multiple stocks)
- [ ] Historical report archive
- [ ] User authentication
- [ ] Custom indicators
- [ ] Mobile app

## License

MIT License - Feel free to use for personal or commercial projects.

## Credits

- **Data Source**: Yahoo Finance (via yfinance)
- **AI Engine**: Anthropic Claude Sonnet 4.5
- **Charts**: Chart.js
- **UI Framework**: Bootstrap 5

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check application logs in console

---

**Built with Flask + Claude AI | Production Ready | Demo Optimized**
