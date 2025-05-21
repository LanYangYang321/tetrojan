# This file will contain the TradeExecutor class.
import random
import datetime
from trading_bot.risk_logger import BOT_LOGGER

class TradeExecutor:
    """
    交易执行器，负责将策略信号转化为实际交易指令并执行。
    """
    def __init__(self, exchange_api, config: dict = None):
        self.logger = BOT_LOGGER
        self.exchange_api = exchange_api  # 交易所API接口 (Placeholder for now)
        self.config = config or {}
        self.orders = {}  # 订单管理 {order_id: order_details}
        self.positions = {}  # 持仓管理 {symbol: position_details}
        self.logger.info(f"交易执行器已初始化。交易所API: {exchange_api}, 配置: {self.config}")

    def execute_signal(self, signal: dict) -> dict:
        """
        执行交易信号
        Input signal format (example):
        {
            "symbol": "BTC/USDT",
            "action": "BUY", # BUY, SELL, HOLD
            "quantity": 0.01,
            "price": 50000, # Optional, for limit orders
            "order_type": "LIMIT", # LIMIT, MARKET
            "strategy_name": "MovingAverageCrossover"
        }
        Output format (example):
        {
            "订单ID": "sim_12345",
            "交易对": "BTC/USDT",
            "方向": "买入", # "买入", "卖出"
            "类型": "限价单", # "限价单", "市价单"
            "数量": 0.01,
            "价格": 50000,
            "状态": "已提交", # "已提交", "已成交", "部分成交", "已取消", "拒绝"
            "成交均价": None,
            "手续费": None,
            "下单时间": "YYYY-MM-DD HH:MM:SS", # Simulate timestamp
            "来源策略": "均线交叉策略"
        }
        """
        self.logger.info(f"收到执行信号: {signal}")
        if not self._validate_signal(signal):
            self.logger.warning("信号验证失败。")
            return {"状态": "拒绝", "原因": "信号无效"}

        # HOLD signal is valid but should not proceed to order creation/submission
        if signal["action"] == "HOLD":
            self.logger.info("信号为HOLD，未执行交易。") # This duplicates the one in _create_order if called before, adjust.
            return {"状态": "已处理", "订单ID": None, "原因": "HOLD信号，未执行交易"}

        order = self._create_order(signal)
        # _create_order can return None if signal action was HOLD
        if not order:
            self.logger.warning("订单创建失败或信号为HOLD。") # Combined message
            return {"状态": "拒绝", "订单ID": None, "原因": "订单创建失败或信号为HOLD"}

        result = self._submit_order(order)
        
        if result.get("状态") in ["已提交", "已成交"]: # Simplified logic for now
            self._update_position(order, result)
        
        self.logger.info(f"执行结果: {result}")
        return result

    def _validate_signal(self, signal: dict) -> bool:
        """
        验证交易信号是否有效
        """
        self.logger.debug(f"验证信号: {signal}")
        required_keys = ["symbol", "action", "quantity", "order_type", "strategy_name"]
        if not all(key in signal for key in required_keys):
            self.logger.warning(f"信号缺少必要键。需要: {required_keys}")
            return False
        if signal["action"] not in ["BUY", "SELL", "HOLD"]:
            self.logger.warning(f"无效的动作: {signal['action']}")
            return False
        if signal["order_type"] not in ["LIMIT", "MARKET"]:
            self.logger.warning(f"无效的订单类型: {signal['order_type']}")
            return False
        
        # HOLD action is valid, but does not require quantity/price checks related to execution
        if signal["action"] == "HOLD":
            self.logger.info("信号为HOLD，验证通过。")
            return True

        if not isinstance(signal["quantity"], (int, float)) or signal["quantity"] <= 0:
            self.logger.warning(f"无效的数量: {signal['quantity']}")
            return False
        if signal["order_type"] == "LIMIT" and (not isinstance(signal.get("price"), (int, float)) or signal.get("price") <= 0):
            self.logger.warning(f"限价单价格无效: {signal.get('price')}")
            return False
        self.logger.info("信号验证成功。")
        return True

    def _create_order(self, signal: dict) -> dict:
        """
        根据信号创建订单 (Placeholder)
        """
        self.logger.info(f"根据信号创建订单: {signal}")
        if signal["action"] == "HOLD": 
            self.logger.info("操作为HOLD，未创建订单。")
            return None 

        order_id = f"sim_{random.randint(10000, 99999)}"
        order_details = {
            "订单ID": order_id,
            "交易对": signal["symbol"],
            "方向": "买入" if signal["action"] == "BUY" else "卖出",
            "类型": "限价单" if signal["order_type"] == "LIMIT" else "市价单",
            "数量": signal["quantity"],
            "价格": signal.get("price") if signal["order_type"] == "LIMIT" else None,
            "状态": "待提交",
            "下单时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "来源策略": signal["strategy_name"]
        }
        self.logger.info(f"订单已创建: {order_details}")
        return order_details

    def _submit_order(self, order: dict) -> dict:
        """
        提交订单到交易所 (Placeholder - Simulate submission)
        """
        self.logger.info(f"提交订单: {order}")
        # Simulate submission to an exchange
        # In a real scenario, this would involve an API call
        submitted_order = order.copy()
        submitted_order["状态"] = "已提交" # Simulate successful submission
        
        # Simulate potential immediate execution for MARKET orders or quick LIMIT fills
        if submitted_order["类型"] == "市价单":
            submitted_order["状态"] = "已成交"
            # Simulate a fill price for market order. In reality, this comes from exchange.
            simulated_fill_price = submitted_order["价格"] if submitted_order["价格"] else (50000 + random.uniform(-100, 100)) 
            submitted_order["成交均价"] = simulated_fill_price
            submitted_order["手续费"] = submitted_order["数量"] * simulated_fill_price * 0.001 # Simulate fee based on value
        elif submitted_order["类型"] == "限价单" and random.choice([True, False]): # Simulate some limit orders getting filled
             submitted_order["状态"] = "已成交"
             submitted_order["成交均价"] = submitted_order["价格"] # Assume filled at specified price
             submitted_order["手续费"] = submitted_order["数量"] * submitted_order["价格"] * 0.001 # Simulate fee based on value

        self.orders[submitted_order["订单ID"]] = submitted_order
        self.logger.info(f"订单已提交，当前状态: {submitted_order['状态']}")
        return submitted_order

    def _update_position(self, order: dict, execution_result: dict):
        """
        更新持仓信息 (Placeholder)
        """
        self.logger.info(f"根据订单更新持仓: {order}，执行结果: {execution_result}")
        if execution_result.get("状态") != "已成交":
            self.logger.info("订单未成交，持仓未更新。")
            return

        symbol = order["交易对"]
        order_qty = order["数量"]
        # Use actual fill price from execution_result
        order_price = execution_result.get("成交均价") 
        if order_price is None: # Should not happen for filled orders
            self.logger.error("错误：订单已成交但未找到成交价格。持仓未更新。") # Changed from print to logger.error
            return

        direction = 1 if order["方向"] == "买入" else -1

        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0.0, "average_price": 0.0, "pnl": 0.0}
        
        current_pos = self.positions[symbol]
        current_quantity = current_pos["quantity"]
        current_avg_price = current_pos["average_price"]
        
        trade_value = order_qty * order_price
        
        if (current_quantity > 0 and direction == -1 and order_qty >= current_quantity) or \
           (current_quantity < 0 and direction == 1 and order_qty >= abs(current_quantity)):
            # Position is being closed or flipped
            realized_pnl = (order_price - current_avg_price) * current_quantity * direction if current_quantity != 0 else 0
            current_pos["pnl"] += realized_pnl # Add to cumulative PnL
            self.logger.info(f"该笔交易实现盈亏: {realized_pnl:.2f}") # Assuming PnL is float
            
            new_quantity = current_quantity + (order_qty * direction)
            if new_quantity == 0:
                current_pos["average_price"] = 0.0
            else: # Flipped position
                current_pos["average_price"] = order_price
        elif current_quantity * direction >= 0: # Increasing position or opening new
            total_quantity = current_quantity + (order_qty * direction)
            if total_quantity != 0:
                current_pos["average_price"] = ((current_avg_price * current_quantity) + 
                                               (order_price * order_qty * direction)) / total_quantity
            else: # This case should be handled by closing logic, but as a fallback
                current_pos["average_price"] = 0
        else: # Reducing position (partial close)
            realized_pnl = (order_price - current_avg_price) * order_qty * (-direction) # Selling part of long, or buying back part of short
            current_pos["pnl"] += realized_pnl
            self.logger.info(f"该笔部分平仓实现盈亏: {realized_pnl:.2f}") # Assuming PnL is float
            # Average price of remaining position does not change

        current_pos["quantity"] += order_qty * direction
        
        if abs(current_pos["quantity"]) < 1e-9: # Effectively zero
            self.logger.info(f"交易对 {symbol} 的持仓已平仓。最终盈亏: {current_pos['pnl']:.2f}")
            # Optionally, remove the symbol from positions if it's truly closed and PnL is tracked elsewhere
            # For now, keep it to see cumulative PnL. Or, del self.positions[symbol]
            current_pos["quantity"] = 0.0 # Set to exact zero
            current_pos["average_price"] = 0.0
        else:
            self.logger.info(f"交易对 {symbol} 的持仓已更新: {self.positions[symbol]}")

    def get_positions(self) -> dict:
        """
        获取当前持仓
        """
        self.logger.debug(f"获取当前持仓: {self.positions}")
        return self.positions.copy()

    def get_orders(self, status: str = None) -> dict:
        """
        获取订单信息
        status: "已提交", "已成交", "已取消", etc. (Optional filter)
        """
        self.logger.debug(f"获取订单信息。状态筛选: {status}")
        if status:
            return {order_id: od for order_id, od in self.orders.items() if od["状态"] == status}
        return self.orders.copy()

    def cancel_order(self, order_id: str) -> dict:
        """
        取消订单 (Placeholder)
        """
        self.logger.info(f"尝试取消订单: {order_id}")
        if order_id in self.orders:
            if self.orders[order_id]["状态"] == "已提交": # Only cancelable if pending
                self.orders[order_id]["状态"] = "已取消"
                self.logger.info(f"订单 {order_id} 已取消。")
                return {"订单ID": order_id, "状态": "已取消"}
            else:
                self.logger.warning(f"订单 {order_id} 无法取消，状态: {self.orders[order_id]['状态']}")
                return {"订单ID": order_id, "状态": self.orders[order_id]["状态"], "原因": "订单不可取消"}
        else:
            self.logger.warning(f"订单 {order_id} 未找到。")
            return {"订单ID": order_id, "状态": "未找到"}
