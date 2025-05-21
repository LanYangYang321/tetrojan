# This file will contain the DataCollector class.
import pandas as pd
import numpy as np
import datetime

def fetch_mock_ohlcv_data(symbol: str, timeframe: str = '1m', limit: int = 100) -> pd.DataFrame:
    """
    Generates mock OHLCV (Open, High, Low, Close, Volume) data for a given symbol.
    This simulates fetching data from an exchange like Binance.

    Args:
        symbol (str): The trading symbol (e.g., 'BTC/USDT').
        timeframe (str): The timeframe for K-lines (e.g., '1m', '5m', '1h').
        limit (int): The number of data points (K-lines) to generate.

    Returns:
        pd.DataFrame: A DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
                      Index is a DatetimeIndex.
    """
    print(f"Fetching mock OHLCV data for {symbol}, timeframe {timeframe}, limit {limit}")

    # Generate a DatetimeIndex
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Determine time_delta based on timeframe string
    if 'h' in timeframe:
        time_delta = pd.Timedelta(hours=int(timeframe.replace('h','')))
    elif 'd' in timeframe:
        time_delta = pd.Timedelta(days=int(timeframe.replace('d','')))
    elif 'm' in timeframe: # Default to minutes if 'm' is present or no other unit
        try:
            time_delta = pd.Timedelta(minutes=int(timeframe.replace('m','')))
        except ValueError:
            print(f"Warning: Could not parse timeframe '{timeframe}', defaulting to 1 minute.")
            time_delta = pd.Timedelta(minutes=1) # Default fallback
    else: # Default to 1 minute if no unit recognized
        print(f"Warning: Unrecognized timeframe format '{timeframe}', defaulting to 1 minute.")
        time_delta = pd.Timedelta(minutes=1)


    end_time = now
    # Calculate start_time to ensure 'limit' number of periods
    # The first timestamp will be start_time, so we need limit-1 intervals from it.
    start_time = end_time - time_delta * (limit - 1) 
    
    # Create precise timestamps for each period's close
    # Using periods=limit ensures we get exactly 'limit' timestamps.
    timestamps = pd.date_range(start=start_time, periods=limit, freq=time_delta)
    
    data_len = len(timestamps)

    # Generate random data
    # Start with a base price, e.g., 50000 for BTC/USDT
    base_price = 50000 + np.random.randn() * 1000
    if 'ETH' in symbol.upper(): # Adjust base price for ETH
        base_price = 1500 + np.random.randn() * 200
    
    open_prices = np.zeros(data_len)
    high_prices = np.zeros(data_len)
    low_prices = np.zeros(data_len)
    close_prices = np.zeros(data_len)
    # Volume in quote currency (e.g. USDT value of BTC traded) then derive base currency volume
    volumes_quote = np.abs(np.random.normal(loc=100000, scale=50000, size=data_len)) 


    # Simulate price movements
    # Initialize first open price
    if data_len > 0:
      open_prices[0] = base_price + np.random.normal(0, base_price * 0.001) # Small fluctuation for the very first open

    for i in range(data_len):
        if i > 0:
            open_prices[i] = close_prices[i-1] + np.random.normal(0, base_price * 0.0005) # Open fluctuates around previous close
        
        # Ensure high is highest, low is lowest
        # Price movement for the bar, scaled by current price to be more realistic
        price_fluctuation_scale = open_prices[i] * 0.01 # Max 1% move for mock data for a bar
        
        # Simulate close price based on open
        close_prices[i] = open_prices[i] + np.random.normal(0, price_fluctuation_scale / 2) # Close tends to be near open

        # Determine high and low relative to open and close
        high_prices[i] = max(open_prices[i], close_prices[i]) + np.abs(np.random.normal(0, price_fluctuation_scale / 4))
        low_prices[i] = min(open_prices[i], close_prices[i]) - np.abs(np.random.normal(0, price_fluctuation_scale / 4))
        
        # Ensure OHLC consistency (e.g., low <= open, high >= close etc.)
        # And high is the max, low is the min of the period
        _o, _h, _l, _c = open_prices[i], high_prices[i], low_prices[i], close_prices[i]
        
        high_prices[i] = max(_o, _c, _h)
        low_prices[i] = min(_o, _c, _l)
        
        # If by chance low > open or low > close after adjustments (should be rare with current logic)
        if low_prices[i] > open_prices[i]: open_prices[i] = low_prices[i] # Adjust open down to low
        if low_prices[i] > close_prices[i]: close_prices[i] = low_prices[i] # Adjust close down to low

        # If by chance high < open or high < close
        if high_prices[i] < open_prices[i]: open_prices[i] = high_prices[i] # Adjust open up to high
        if high_prices[i] < close_prices[i]: close_prices[i] = high_prices[i] # Adjust close up to high

    # Calculate volume in base currency (e.g. BTC)
    # Using average price of the bar for conversion
    avg_price_for_bar = (open_prices + close_prices) / 2
    volumes_base = volumes_quote / np.where(avg_price_for_bar == 0, 1, avg_price_for_bar) # Avoid division by zero if price is 0


    df = pd.DataFrame({
        'timestamp': timestamps, # Timestamp is the closing time of the bar
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes_base # Volume in base currency (e.g. BTC)
    })
    
    df.set_index('timestamp', inplace=True)

    print(f"Generated mock data for {symbol}:\n{df.head()}")
    return df

if __name__ == '__main__':
    # Example usage:
    mock_data_btc = fetch_mock_ohlcv_data('BTC/USDT', timeframe='1m', limit=5)
    print("\nBTC/USDT 1m Mock Data:")
    print(mock_data_btc)

    mock_data_eth = fetch_mock_ohlcv_data('ETH/USDT', timeframe='5m', limit=3)
    print("\nETH/USDT 5m Mock Data:")
    print(mock_data_eth)

    mock_data_sol = fetch_mock_ohlcv_data('SOL/USDT', timeframe='1h', limit=4)
    print("\nSOL/USDT 1h Mock Data:")
    print(mock_data_sol)

    mock_data_day = fetch_mock_ohlcv_data('ADA/USDT', timeframe='1d', limit=2)
    print("\nADA/USDT 1d Mock Data:")
    print(mock_data_day)

    # Test edge case with potentially problematic timeframe string
    mock_data_custom_tf = fetch_mock_ohlcv_data('LINK/USDT', timeframe='15', limit=2) # Should default to minutes
    print("\nLINK/USDT '15' (defaulted to 15m) Mock Data:")
    print(mock_data_custom_tf)

    mock_data_custom_tf_unknown = fetch_mock_ohlcv_data('DOT/USDT', timeframe='2x', limit=2) # Should default to 1m
    print("\nDOT/USDT '2x' (defaulted to 1m) Mock Data:")
    print(mock_data_custom_tf_unknown)
