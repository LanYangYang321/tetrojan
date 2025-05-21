# trading_bot/config.py

import os

# -----------------------------------------------------------------------------
# API Key Configuration (Placeholders - DO NOT COMMIT REAL KEYS)
# -----------------------------------------------------------------------------
# In a real application, use environment variables or a secure vault.
# Example: BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_API_KEY = "YOUR_BINANCE_API_KEY_HERE"  # Placeholder
BINANCE_API_SECRET = "YOUR_BINANCE_API_SECRET_HERE"  # Placeholder

# Configuration for LLM API (if applicable)
LLM_API_KEY = "YOUR_LLM_API_KEY_HERE" # Placeholder
LLM_API_ENDPOINT = "YOUR_LLM_API_ENDPOINT_HERE" # Placeholder

# -----------------------------------------------------------------------------
# Main Loop Configuration
# -----------------------------------------------------------------------------
def get_main_loop_config() -> dict:
    return {
        "trading_symbol": "BTC/USDT",  # Default symbol to trade
        "loop_interval_seconds": 60,  # Time in seconds between each trading loop iteration
        "max_runs": 5,  # Max iterations for testing; set float('inf') for continuous
        "data_fetch_limit": 100, # Number of K-lines to fetch for analysis
        "data_timeframe": "1m" # Timeframe for K-lines (e.g., '1m', '5m', '1h')
    }

# -----------------------------------------------------------------------------
# Strategy Configurations
# -----------------------------------------------------------------------------
def get_strategy_configs() -> dict:
    return {
        "MovingAverageCrossover": {
            "short_window": 10,
            "long_window": 30,
            "order_quantity": 0.001, # Example: 0.001 BTC
            "order_type": "MARKET", # MARKET or LIMIT
            "description": "Trend Following via MA Crossover"
        },
        "ChannelBreakout": {
            "window": 20, # Lookback period for high/low
            "order_quantity": 0.001,
            "order_type": "MARKET",
            "description": "Trend Breakout from recent High/Low"
        },
        "BollingerBandsMeanReversion": {
            "window": 20,
            "num_std_dev": 2.0,
            "order_quantity": 0.001,
            "order_type": "MARKET",
            "description": "Range Reversion using Bollinger Bands"
        },
        "GridTrading": {
            "num_levels": 5, # Number of grid levels above and below current price
            "grid_spacing_percentage": 0.005, # 0.5% spacing between grid lines
            "order_quantity_per_level": 0.0002, # Quantity for each grid order
            "order_type": "LIMIT",
            "description": "Range Grid Trading"
        },
        "LlmApiConfig": { # Configuration for the LLM API call, if needed by llm_interface.py
            "model_name": "market-state-identifier-v1",
            "api_key": LLM_API_KEY, # Using placeholder from above
            "endpoint": LLM_API_ENDPOINT,
            "timeout_seconds": 30
        }
        # Add other strategy configurations here
    }

# -----------------------------------------------------------------------------
# Trade Executor Configuration
# -----------------------------------------------------------------------------
def get_trade_executor_config() -> dict:
    return {
        "exchange_name": "Binance", # Or "BinanceFutures" etc.
        "simulation_mode": True, # True for paper trading/simulation, False for live
        "slippage_percentage": 0.001, # 0.1% simulated slippage for market orders
        "api_key": BINANCE_API_KEY, # Using placeholder
        "api_secret": BINANCE_API_SECRET, # Using placeholder
        # Add other executor related params like rate limits, retry attempts etc.
    }

# -----------------------------------------------------------------------------
# Risk Management Configuration
# -----------------------------------------------------------------------------
def get_risk_configs() -> dict:
    return {
        "max_order_sizes": { # Max quantity per single order
            "BTC/USDT": 0.1,   # Max 0.1 BTC per order
            "ETH/USDT": 2.0,   # Max 2 ETH per order
            "default": 0.05    # Default max for other symbols (e.g. if trading 0.05 of base currency)
        },
        "max_total_exposure_usd": 5000.00, # Max total portfolio value in USD
        "max_drawdown_percentage_session": 5.0, # Max % loss for the current session/day
        "stop_loss_percentage_per_trade": 1.0, # e.g. 1% stop loss from entry price
        "take_profit_percentage_per_trade": 2.0, # e.g. 2% take profit from entry price
        "default_order_quantity": 0.001, # Fallback quantity if not defined in strategy
    }

# -----------------------------------------------------------------------------
# Example of how to access configurations (for documentation/testing)
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("--- 主循环配置 ---")
    main_cfg = get_main_loop_config()
    print(main_cfg)

    print("\n--- 策略配置 ---")
    strat_cfgs = get_strategy_configs()
    for name, params in strat_cfgs.items():
        print(f"策略: {name}, 参数: {params}")

    print("\n--- 交易执行器配置 ---")
    exec_cfg = get_trade_executor_config()
    print(exec_cfg)

    print("\n--- 风险配置 ---")
    risk_cfg = get_risk_configs()
    print(risk_cfg)
    
    print(f"\n访问示例: 移动平均线交叉策略 短窗口 -> {strat_cfgs['MovingAverageCrossover']['short_window']}")
    print(f"访问示例: 默认最大订单大小 -> {risk_cfg['max_order_sizes']['default']}")
    print(f"访问示例: 交易符号 -> {main_cfg['trading_symbol']}")
