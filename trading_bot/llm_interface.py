# This file will contain the LLMInterface class.
import pandas as pd
import random

def get_market_state(market_data: pd.DataFrame, llm_config: dict = None) -> dict:
    """
    Simulates calling a cloud-based Large Language Model (LLM) to determine the market state.

    Args:
        market_data (pd.DataFrame): A DataFrame containing historical market data (OHLCV).
                                    It's assumed to have 'close' prices and other relevant features
                                    that an LLM might use.
        llm_config (dict, optional): Configuration for the LLM API call (e.g., model name, API key).
                                     Not used in this mock implementation.

    Returns:
        dict: A dictionary containing the market state and confidence.
              Example: {"market_state": "Trend", "confidence": 0.85, "details": "Uptrend identified"}
                       {"market_state": "Range", "confidence": 0.70, "details": "Sideways movement observed"}
    """
    print(f"LLM接口：收到包含 {len(market_data)} 行的市场数据。最新收盘价: {market_data['close'].iloc[-1] if not market_data.empty else '无'}")
    if llm_config:
        print(f"LLM 配置: {llm_config}")

    # --- Mock LLM Logic ---
    # In a real implementation, this would involve:
    # 1. Preprocessing `market_data` into features suitable for the LLM.
    # 2. Making an API call to the LLM service.
    # 3. Parsing the LLM's response.

    # For now, let's simulate based on a very simple rule or randomly.
    # Simple rule: if the price changed by more than X% in the last Y periods, it's a trend.
    
    possible_states = ["Trend", "Range"]
    chosen_state = random.choice(possible_states)
    confidence = round(random.uniform(0.65, 0.95), 2)
    details = ""

    if not market_data.empty and len(market_data) > 10: # Need some data to even try a rule
        # Ensure index is sorted if not already, for correct iloc selection
        # market_data = market_data.sort_index() # Assuming timestamp index, should be sorted by fetcher

        # Using .iloc[-1] for the latest, and .iloc[-11] for 10 periods prior to the latest.
        price_change_percentage = (market_data['close'].iloc[-1] - market_data['close'].iloc[-11]) / market_data['close'].iloc[-11]
        
        if abs(price_change_percentage) > 0.02: # If price changed by more than 2% in last 10 periods
            if price_change_percentage > 0:
                chosen_state = "Trend"
                details = "近期价格显著上涨，判断为上升趋势。"
            else:
                chosen_state = "Trend"
                details = "近期价格显著下跌，判断为下降趋势。"
        else:
            chosen_state = "Range"
            details = "价格波动较小，判断为震荡市场。"
    else:
        # Not enough data, rely on random choice
        if chosen_state == "Trend":
            details = "趋势（数据不足，随机选择）。"
        else:
            details = "震荡（数据不足，随机选择）。"


    print(f"LLM模拟：市场状态 -> {chosen_state}, 置信度 -> {confidence}, 详情 -> {details}")
    
    return {
        "market_state": chosen_state, # "Trend" or "Range"
        "confidence": confidence,
        "details": details
    }

if __name__ == '__main__':
    # Create some mock data to test
    # This import should be here for the __main__ block
    from trading_bot.data_collector import fetch_mock_ohlcv_data
    
    print("--- 测试用例1：默认模拟数据（可能为震荡或随机）---")
    mock_data_1 = fetch_mock_ohlcv_data('BTC/USDT', limit=20)
    market_state_1 = get_market_state(mock_data_1)
    print(f"返回的市场状态1: {market_state_1}")
    print("\n")

    print("--- 测试用例2：模拟强势上涨趋势 ---")
    mock_data_uptrend = fetch_mock_ohlcv_data('ETH/USDT', limit=20)
    # Manually adjust close prices to show a clear uptrend for the last 10 periods
    if not mock_data_uptrend.empty and len(mock_data_uptrend) >= 11:
        # Ensure we are modifying a copy if it's a view, to avoid SettingWithCopyWarning
        mock_data_uptrend = mock_data_uptrend.copy()
        # The 11th point from the end is iloc[-11]. The 12th is iloc[-12]
        # We want to adjust the last 11 points, including the current last one.
        # So, from iloc[-11] up to iloc[-1]
        base_price_for_trend = mock_data_uptrend['close'].iloc[-12] # Price before the trend starts
        for i in range(1, 12): # Adjusts points from iloc[-11] up to iloc[-1]
            mock_data_uptrend.loc[mock_data_uptrend.index[-i], 'close'] = base_price_for_trend * (1 + 0.005 * (12-i))
    market_state_uptrend = get_market_state(mock_data_uptrend)
    print(f"返回的市场状态（上涨趋势）: {market_state_uptrend}")
    print("\n")

    print("--- 测试用例3：模拟强势下跌趋势 ---")
    mock_data_downtrend = fetch_mock_ohlcv_data('SOL/USDT', limit=20)
    # Manually adjust close prices to show a clear downtrend
    if not mock_data_downtrend.empty and len(mock_data_downtrend) >= 11:
        mock_data_downtrend = mock_data_downtrend.copy()
        base_price_for_trend = mock_data_downtrend['close'].iloc[-12] # Price before the trend starts
        for i in range(1, 12): # Adjusts points from iloc[-11] up to iloc[-1]
            mock_data_downtrend.loc[mock_data_downtrend.index[-i], 'close'] = base_price_for_trend * (1 - 0.005 * (12-i))
    market_state_downtrend = get_market_state(mock_data_downtrend)
    print(f"返回的市场状态（下跌趋势）: {market_state_downtrend}")
    print("\n")
    
    print("--- 测试用例4：空DataFrame ---")
    empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume']) # Ensure columns exist for iloc access
    market_state_empty = get_market_state(empty_df)
    print(f"返回的市场状态（空数据）: {market_state_empty}")

    print("--- Test Case 5: Dataframe with less than 11 rows ---")
    mock_data_short = fetch_mock_ohlcv_data('ADA/USDT', limit=5)
    market_state_short = get_market_state(mock_data_short)
    print(f"Returned Market State (Short Data): {market_state_short}")
