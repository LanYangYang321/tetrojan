# This file will contain the main script to run the trading bot.
import time
import pandas as pd

from trading_bot.data_collector import fetch_mock_ohlcv_data
from trading_bot.llm_interface import get_market_state
from trading_bot.strategy_scheduler import choose_strategy
from trading_bot.trade_executor import TradeExecutor
from trading_bot.risk_logger import BOT_LOGGER, check_max_order_size, check_overall_portfolio_exposure
# The get_main_loop_config will be added to config.py in a subsequent step.
# For now, this import will likely fail if run directly, but the file structure is being prepared.
from trading_bot.config import get_strategy_configs, get_trade_executor_config, get_risk_configs, get_main_loop_config

def main_trading_loop():
    """
    The main loop for the trading bot.
    Runs every minute (configurable) to perform trading operations.
    """
    BOT_LOGGER.info("开始主交易循环...")

    # Initialize configurations
    strategy_configs = get_strategy_configs()
    trade_executor_config = get_trade_executor_config() 
    risk_configs = get_risk_configs()
    main_loop_config = get_main_loop_config() # This function needs to be added to config.py

    # Initialize TradeExecutor
    # For now, exchange_api is a placeholder. In a real scenario, it would be an instance
    # of a Binance API client (e.g., from python-binance library).
    simulated_exchange_api = "SimulatedBinanceAPI_v1" 
    trade_executor = TradeExecutor(exchange_api=simulated_exchange_api, config=trade_executor_config)

    # --- Main Loop ---
    run_count = 0
    max_runs = main_loop_config.get("max_runs", 3) # Limit runs for testing; set to float('inf') for continuous
    loop_interval_seconds = main_loop_config.get("loop_interval_seconds", 60) # Default to 1 minute

    while run_count < max_runs:
        run_count += 1
        BOT_LOGGER.info(f"--- 开始交易循环迭代: {run_count}/{max_runs} ---")
        
        try:
            # 1. Data Input (Fetch market data)
            # Using a fixed symbol for now, can be made configurable
            current_symbol = main_loop_config.get("trading_symbol", "BTC/USDT")
            data_limit = main_loop_config.get("data_fetch_limit", 100) # How many k-lines
            data_timeframe = main_loop_config.get("data_timeframe", "1m") # k-line timeframe
            BOT_LOGGER.info(f"正在为 {current_symbol} 获取市场数据，时间周期 {data_timeframe}，数量 {data_limit}...") # Updated timeframe and limit part
            market_data = fetch_mock_ohlcv_data(symbol=current_symbol, timeframe=data_timeframe, limit=data_limit)
            
            if market_data.empty:
                BOT_LOGGER.warning("未收到市场数据。跳过本次迭代。")
                if run_count < max_runs: time.sleep(loop_interval_seconds)
                continue

            # 2. Call LLM to identify market state
            BOT_LOGGER.info("正在从LLM获取市场状态...")
            llm_output = get_market_state(market_data, llm_config=strategy_configs.get("LlmApiConfig")) # Pass LLM specific config if any
            
            if not llm_output or "market_state" not in llm_output:
                BOT_LOGGER.error("从LLM获取有效市场状态失败。跳过本次迭代。")
                if run_count < max_runs: time.sleep(loop_interval_seconds)
                continue
            BOT_LOGGER.info(f"LLM输出：状态='{llm_output['market_state']}', 置信度={llm_output.get('confidence', '无')}, 详情='{llm_output.get('details', '')}'")

            # 3. Select Strategy based on market state
            BOT_LOGGER.info("正在选择策略...")
            current_strategy = choose_strategy(llm_output, strategy_configs)

            if not current_strategy:
                BOT_LOGGER.warning("未找到适合当前市场状态的策略。跳过交易执行。")
                if run_count < max_runs: time.sleep(loop_interval_seconds)
                continue
            BOT_LOGGER.info(f"已选择策略: {current_strategy.strategy_name}")
            # Ensure the strategy instance has the most up-to-date specific config
            current_strategy.update_config(strategy_configs.get(current_strategy.strategy_name, {})) 

            # 4. Generate Trading Signals from the chosen strategy
            BOT_LOGGER.info("正在生成交易信号...")
            signals_df = current_strategy.generate_signals(market_data) # DataFrame of signals

            if signals_df.empty:
                BOT_LOGGER.info("策略在此期间未生成交易信号。")
                # Optional: Could still proceed to risk checks or portfolio updates if needed
            else:
                BOT_LOGGER.info(f"已生成信号:\n{signals_df.tail()}") # Using .tail() as it was in original for brevity
                
                latest_signal_row = signals_df.iloc[-1] if not signals_df.empty else pd.Series(dtype='object') # Ensure dtype to avoid issues with .get
                
                action = "HOLD" # Default action
                # Assuming 'signal' column: 1 for BUY, -1 for SELL, 0 or absent for HOLD
                signal_value = latest_signal_row.get('signal', 0) 
                if signal_value == 1: action = "BUY"
                elif signal_value == -1: action = "SELL"
                
                if action != "HOLD":
                    # Construct the signal dictionary for the TradeExecutor
                    # Get order quantity from strategy's specific config, then general risk config, then a hardcoded default
                    default_order_qty = risk_configs.get("default_order_quantity", 0.01)
                    strategy_specific_config = strategy_configs.get(current_strategy.strategy_name, {})
                    order_quantity = strategy_specific_config.get("order_quantity", default_order_qty)
                    
                    # Get order type similarly
                    default_order_type = "MARKET"
                    order_type = strategy_specific_config.get("order_type", default_order_type)
                    
                    signal_to_execute = {
                        "symbol": current_symbol,
                        "action": action,
                        "quantity": order_quantity,
                        "order_type": order_type,
                        "price": latest_signal_row.get('price'), # For LIMIT orders, price might come from signal
                        "strategy_name": current_strategy.strategy_name
                    }
                    BOT_LOGGER.info(f"待执行信号: {signal_to_execute}")

                    # 5. Risk Control Checks
                    BOT_LOGGER.info("正在执行风险检查...")
                    proceed_trade = True # Assume true initially

                    # Risk check 1: Max order size
                    if not check_max_order_size(
                        signal_to_execute["symbol"], 
                        signal_to_execute["quantity"], 
                        risk_configs.get("max_order_sizes", {})
                    ):
                        proceed_trade = False
                        BOT_LOGGER.warning(f"由于超出最大订单大小限制，{current_symbol} 的交易已停止。") # Updated this specific message

                    # Risk check 2: Overall exposure (simplified)
                    # This is a very simplified check. A real check needs current market prices for all assets.
                    if proceed_trade: # Only check if previous checks passed
                        # Simulate getting total portfolio value in USD.
                        # In a real system, TradeExecutor would provide this, or another service.
                        current_positions_details = trade_executor.get_positions()
                        current_portfolio_value_simulated = 0
                        for sym, pos_data in current_positions_details.items():
                            # Assuming TradeExecutor's get_positions returns dicts that might have 'average_price' and 'quantity'
                            # This is still a rough estimate without live prices.
                            # For this placeholder, let's assume 'value_usd' might be part of position data from executor in future.
                            # Or, we use a mock price if value_usd is not there.
                            if "value_usd" in pos_data:
                                current_portfolio_value_simulated += pos_data["value_usd"]
                            else: # Fallback to a very rough estimate if value_usd is not present
                                mock_price = 50000 if "BTC" in sym else 1500 # Extremely rough mock price
                                current_portfolio_value_simulated += pos_data.get("quantity",0) * mock_price
                        
                        # Construct the input for check_overall_portfolio_exposure
                        # The function expects a dict like {"symbol": {"value_usd": X}}
                        # We are passing a single entry representing the whole portfolio.
                        mock_positions_for_risk_check = {"portfolio_total": {"value_usd": current_portfolio_value_simulated}}

                        if not check_overall_portfolio_exposure(mock_positions_for_risk_check, risk_configs.get("max_total_exposure_usd", 100000)):
                             proceed_trade = False
                             BOT_LOGGER.warning(f"由于超出总投资组合风险暴露限制，{current_symbol} 的交易已停止。") # Updated current_symbol part

                    if proceed_trade:
                        # 6. Execute Trade via TradeExecutor
                        BOT_LOGGER.info("正在执行交易...")
                        execution_result = trade_executor.execute_signal(signal_to_execute)
                        BOT_LOGGER.info(f"交易执行结果: {execution_result}")
                    else:
                        BOT_LOGGER.warning(f"由于风险检查未通过，{current_symbol} 的交易 (动作: {action}) 已中止。") # Updated action part
                else:
                    BOT_LOGGER.info("操作为持有。无交易执行。")

            # 7. Record & Monitor (logging is done throughout)
            BOT_LOGGER.info(f"当前订单: {trade_executor.get_orders()}")
            BOT_LOGGER.info(f"当前持仓: {trade_executor.get_positions()}")
            BOT_LOGGER.info(f"--- 完成交易循环迭代: {run_count}/{max_runs} ---")

        except Exception as e:
            BOT_LOGGER.error(f"主交易循环迭代 {run_count} 中发生异常: {e}", exc_info=True)
            # Potentially implement more robust error handling, like notifying admin

        if run_count < max_runs: # Avoid sleeping after the last run
            BOT_LOGGER.info(f"休眠 {loop_interval_seconds} 秒后进入下一次迭代...")
            time.sleep(loop_interval_seconds)
    
    BOT_LOGGER.info(f"主交易循环在 {max_runs} 次运行后结束。") # Updated this line

if __name__ == '__main__':
    BOT_LOGGER.info("交易机器人应用开始启动...")
    try:
        main_trading_loop()
    except ImportError as e:
        BOT_LOGGER.critical(f"无法导入必要的模块。请确保所有组件都已正确放置并且 config.py 已更新: {e}", exc_info=True) # Updated this line
    except KeyboardInterrupt:
        BOT_LOGGER.info("交易机器人应用被用户中断 (KeyboardInterrupt)。")
    except Exception as e:
        BOT_LOGGER.critical(f"交易机器人应用因未处理的异常而失败: {e}", exc_info=True)
    finally:
        BOT_LOGGER.info("交易机器人应用已关闭。")
