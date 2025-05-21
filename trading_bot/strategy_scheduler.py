# This file will contain the StrategyScheduler class.
from trading_bot.strategy_library import (
    BaseStrategy, 
    MovingAverageCrossoverStrategy, 
    ChannelBreakoutStrategy,
    BollingerBandsMeanReversionStrategy,
    GridTradingStrategy
)
# Import other strategies if/when they are added

def choose_strategy(market_state_info: dict, strategy_configs: dict) -> BaseStrategy:
    """
    Selects and instantiates a trading strategy based on the identified market state.

    Args:
        market_state_info (dict): Information about the market state from the LLM.
                                  Expected format: {"market_state": "Trend" or "Range", 
                                                    "confidence": float, 
                                                    "details": str}
        strategy_configs (dict): A dictionary containing configurations for each strategy.
                                 Example: 
                                 {
                                     "MovingAverageCrossover": {"short_window": 10, "long_window": 30},
                                     "ChannelBreakout": {"window": 20},
                                     "BollingerBandsMeanReversion": {"window": 20, "num_std_dev": 2},
                                     "GridTrading": {"levels": 5, "width": 0.01}
                                 }

    Returns:
        BaseStrategy: An instance of the chosen trading strategy, or None if no suitable strategy is found.
    """
    market_state = market_state_info.get("market_state")
    confidence = market_state_info.get("confidence", 0.0)
    
    print(f"Strategy Scheduler: Choosing strategy for market state '{market_state}' with confidence {confidence:.2f}")

    chosen_strategy_instance = None

    # Basic logic:
    # If Trend -> Use Trend-following strategies
    # If Range -> Use Range-bound/Mean-reversion strategies
    # We can add more sophisticated logic later, e.g., based on confidence or specific details from LLM

    if market_state == "Trend":
        # Example: Prioritize MovingAverageCrossover for Trend
        # Could also randomly pick between trend strategies or use a more specific rule
        config = strategy_configs.get("MovingAverageCrossover", {})
        chosen_strategy_instance = MovingAverageCrossoverStrategy(config=config)
        print(f"Selected Trend strategy: {chosen_strategy_instance.strategy_name} with config: {config}")
        # As an alternative, one could also pick ChannelBreakout for Trend
        # config_cb = strategy_configs.get("ChannelBreakout", {})
        # chosen_strategy_instance = ChannelBreakoutStrategy(config=config_cb)
        # print(f"Selected Trend strategy: {chosen_strategy_instance.strategy_name} with config: {config_cb}")

    elif market_state == "Range":
        # Example: Prioritize BollingerBandsMeanReversion for Range
        config = strategy_configs.get("BollingerBandsMeanReversion", {})
        chosen_strategy_instance = BollingerBandsMeanReversionStrategy(config=config)
        print(f"Selected Range strategy: {chosen_strategy_instance.strategy_name} with config: {config}")
        # As an alternative, one could also pick GridTrading for Range
        # config_gt = strategy_configs.get("GridTrading", {})
        # chosen_strategy_instance = GridTradingStrategy(config=config_gt)
        # print(f"Selected Range strategy: {chosen_strategy_instance.strategy_name} with config: {config_gt}")
    else:
        print(f"Warning: Unknown market state '{market_state}'. No strategy selected.")
        # Optionally, define a default strategy or return None
        return None

    if chosen_strategy_instance:
        print(f"Strategy chosen: {chosen_strategy_instance.strategy_name}")
    
    return chosen_strategy_instance

if __name__ == '__main__':
    # Example configurations for strategies
    mock_strategy_configs = {
        "MovingAverageCrossover": {"short_window": 10, "long_window": 30, "description": "Trend Following"},
        "ChannelBreakout": {"window": 20, "description": "Trend Breakout"},
        "BollingerBandsMeanReversion": {"window": 20, "num_std_dev": 2, "description": "Range Reversion"},
        "GridTrading": {"levels": 5, "width": 0.01, "description": "Range Grid"}
    }

    print("--- Test Case 1: Market State 'Trend' ---")
    llm_output_trend = {"market_state": "Trend", "confidence": 0.80, "details": "Strong uptrend identified"}
    selected_strategy_trend = choose_strategy(llm_output_trend, mock_strategy_configs)
    if selected_strategy_trend:
        print(f"Main Test: Selected strategy for Trend: {selected_strategy_trend.strategy_name}, Config: {selected_strategy_trend.get_config()}")
        # Test generating signals (will be placeholder)
        import pandas as pd # Import pandas here for the test block
        mock_market_data = pd.DataFrame({'close': [10,11,12,13,14,15]}) # Minimal data for placeholder
        selected_strategy_trend.generate_signals(mock_market_data)
    print("\n")

    print("--- Test Case 2: Market State 'Range' ---")
    llm_output_range = {"market_state": "Range", "confidence": 0.75, "details": "Sideways movement in a narrow band"}
    selected_strategy_range = choose_strategy(llm_output_range, mock_strategy_configs)
    if selected_strategy_range:
        print(f"Main Test: Selected strategy for Range: {selected_strategy_range.strategy_name}, Config: {selected_strategy_range.get_config()}")
        import pandas as pd # Import pandas here for the test block
        mock_market_data = pd.DataFrame({'close': [12,12.1,11.9,12.05,11.95,12]}) # Minimal data
        selected_strategy_range.generate_signals(mock_market_data)
    print("\n")

    print("--- Test Case 3: Market State 'Unknown' ---")
    llm_output_unknown = {"market_state": "Consolidating", "confidence": 0.60, "details": "Price is undecided"}
    selected_strategy_unknown = choose_strategy(llm_output_unknown, mock_strategy_configs)
    if selected_strategy_unknown:
        print(f"Main Test: Selected strategy for Unknown: {selected_strategy_unknown.strategy_name}")
    else:
        print("Main Test: No strategy selected for Unknown state, as expected.")
    print("\n")
    
    print("--- Test Case 4: Market State 'Trend' but config missing for primary choice ---")
    # To test fallback or error handling if primary chosen strategy config is missing
    # Current choose_strategy will use {} if config is missing.
    current_trend_config = mock_strategy_configs.pop("MovingAverageCrossover", None) # Remove temporarily
    selected_strategy_trend_no_config = choose_strategy(llm_output_trend, mock_strategy_configs)
    if selected_strategy_trend_no_config:
         print(f"Main Test: Selected strategy for Trend (no specific MA config): {selected_strategy_trend_no_config.strategy_name}, Config: {selected_strategy_trend_no_config.get_config()}")
    if current_trend_config: mock_strategy_configs["MovingAverageCrossover"] = current_trend_config # Add back
    print("\n")
