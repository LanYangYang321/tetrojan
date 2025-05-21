# This file will contain the TradeExecutor class.
import random
import datetime

class TradeExecutor:
    """
    交易执行器，负责将策略信号转化为实际交易指令并执行。
    """
    def __init__(self, exchange_api, config: dict = None):
        self.exchange_api = exchange_api  # 交易所API接口 (Placeholder for now)
        self.config = config or {}
        self.orders = {}  # 订单管理 {order_id: order_details}
        self.positions = {}  # 持仓管理 {symbol: position_details}
        print(f"TradeExecutor initialized with exchange_api: {exchange_api} and config: {self.config}")

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
        print(f"Received signal to execute: {signal}")
        if not self._validate_signal(signal):
            print("Signal validation failed.")
            print("Signal validation failed.")
            return {"状态": "拒绝", "原因": "信号无效"}

        # HOLD signal is valid but should not proceed to order creation/submission
        if signal["action"] == "HOLD":
            BOT_LOGGER.info("HOLD signal received by TradeExecutor. No trade action will be taken.")
            return {"状态": "已处理", "订单ID": None, "原因": "HOLD信号，未执行交易"}

        order = self._create_order(signal)
        # _create_order can return None if signal action was HOLD and somehow bypassed the check above,
        # or for other internal reasons if expanded later.
        if not order:
            BOT_LOGGER.warning("Order creation failed or signal was HOLD. No order to submit.")
            return {"状态": "拒绝", "订单ID": None, "原因": "订单创建失败或信号为HOLD"}

        result = self._submit_order(order)
        
        if result.get("状态") in ["已提交", "已成交"]: # Simplified logic for now
            self._update_position(order, result)
        
        print(f"Execution result: {result}")
        return result

    def _validate_signal(self, signal: dict) -> bool:
        """
        验证交易信号是否有效
        """
        print(f"Validating signal: {signal}")
        required_keys = ["symbol", "action", "quantity", "order_type", "strategy_name"]
        if not all(key in signal for key in required_keys):
            print(f"Signal missing required keys. Required: {required_keys}")
            return False
        if signal["action"] not in ["BUY", "SELL", "HOLD"]:
            print(f"Invalid action: {signal['action']}")
            return False
        if signal["order_type"] not in ["LIMIT", "MARKET"]:
            print(f"Invalid order_type: {signal['order_type']}")
            return False
        
        # HOLD action is valid, but does not require quantity/price checks related to execution
        if signal["action"] == "HOLD":
            print("Signal is HOLD, validation successful.")
            return True

        if not isinstance(signal["quantity"], (int, float)) or signal["quantity"] <= 0:
            print(f"Invalid quantity: {signal['quantity']}")
            return False
        if signal["order_type"] == "LIMIT" and (not isinstance(signal.get("price"), (int, float)) or signal.get("price") <= 0):
            print(f"Invalid price for LIMIT order: {signal.get('price')}")
            return False
        print("Signal validated successfully.")
        return True

    def _create_order(self, signal: dict) -> dict:
        """
        根据信号创建订单 (Placeholder)
        """
        print(f"Creating order from signal: {signal}")
        if signal["action"] == "HOLD": # Should not happen if execute_signal filters it
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
        print(f"Order created: {order_details}")
        return order_details

    def _submit_order(self, order: dict) -> dict:
        """
        提交订单到交易所 (Placeholder - Simulate submission)
        """
        print(f"Submitting order: {order}")
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
        print(f"Order submitted, current status: {submitted_order['状态']}")
        return submitted_order

    def _update_position(self, order: dict, execution_result: dict):
        """
        更新持仓信息 (Placeholder)
        """
        print(f"Updating position based on order: {order} and execution result: {execution_result}")
        if execution_result.get("状态") != "已成交":
            print("Order not filled, position not updated.")
            return

        symbol = order["交易对"]
        order_qty = order["数量"]
        # Use actual fill price from execution_result
        order_price = execution_result.get("成交均价") 
        if order_price is None: # Should not happen for filled orders
            print("Error: Order filled but no fill price found. Position not updated.")
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
            print(f"Realized PnL for this trade: {realized_pnl}")
            
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
            print(f"Realized PnL for this partial close: {realized_pnl}")
            # Average price of remaining position does not change

        current_pos["quantity"] += order_qty * direction
        
        if abs(current_pos["quantity"]) < 1e-9: # Effectively zero
            print(f"Position for {symbol} closed. Final PnL for {symbol}: {current_pos['pnl']}")
            # Optionally, remove the symbol from positions if it's truly closed and PnL is tracked elsewhere
            # For now, keep it to see cumulative PnL. Or, del self.positions[symbol]
            current_pos["quantity"] = 0.0 # Set to exact zero
            current_pos["average_price"] = 0.0
        else:
            print(f"Position for {symbol} updated: {self.positions[symbol]}")

    def get_positions(self) -> dict:
        """
        获取当前持仓
        """
        print(f"Fetching current positions: {self.positions}")
        return self.positions.copy()

    def get_orders(self, status: str = None) -> dict:
        """
        获取订单信息
        status: "已提交", "已成交", "已取消", etc. (Optional filter)
        """
        print(f"Fetching orders. Filter by status: {status}")
        if status:
            return {order_id: od for order_id, od in self.orders.items() if od["状态"] == status}
        return self.orders.copy()

    def cancel_order(self, order_id: str) -> dict:
        """
        取消订单 (Placeholder)
        """
        print(f"Attempting to cancel order: {order_id}")
        if order_id in self.orders:
            if self.orders[order_id]["状态"] == "已提交": # Only cancelable if pending
                self.orders[order_id]["状态"] = "已取消"
                print(f"Order {order_id} cancelled.")
                return {"订单ID": order_id, "状态": "已取消"}
            else:
                print(f"Order {order_id} cannot be cancelled, status: {self.orders[order_id]['状态']}")
                return {"订单ID": order_id, "状态": self.orders[order_id]["状态"], "原因": "订单不可取消"}
        else:
            print(f"Order {order_id} not found.")
            return {"订单ID": order_id, "状态": "未找到"}
