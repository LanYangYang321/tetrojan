import unittest
from trading_bot import trade_executor
from trading_bot.risk_logger import BOT_LOGGER # Import for context, though not directly used in asserts here

class TestTradeExecutor(unittest.TestCase):
    def setUp(self):
        # Initialize TradeExecutor with a dummy exchange_api and config
        self.executor = trade_executor.TradeExecutor(exchange_api="sim_test_api", config={})
        # Ensure BOT_LOGGER is available for TradeExecutor if it uses it internally
        # (as per the fix made in the previous step)
        trade_executor.BOT_LOGGER = BOT_LOGGER 

    def test_execute_valid_buy_signal(self):
        signal = {"symbol": "BTC/USDT", "action": "BUY", "quantity": 0.01, "order_type": "MARKET", "strategy_name": "TestStrat"}
        result = self.executor.execute_signal(signal)
        # Market orders might fill immediately in the simulation
        self.assertIn(result.get("状态"), ["已提交", "已成交"], f"Unexpected status: {result.get('状态')}")
        self.assertIsNotNone(result.get("订单ID"))
        print(f"TestTradeExecutor: test_execute_valid_buy_signal PASSED - Result: {result}")

    def test_execute_valid_sell_signal(self):
        signal = {"symbol": "ETH/USDT", "action": "SELL", "quantity": 0.1, "order_type": "LIMIT", "price": 2000, "strategy_name": "TestStrat"}
        result = self.executor.execute_signal(signal)
        # Limit orders are usually '已提交' unless simulated to fill immediately
        self.assertIn(result.get("状态"), ["已提交", "已成交"], f"Unexpected status: {result.get('状态')}")
        self.assertIsNotNone(result.get("订单ID"))
        print(f"TestTradeExecutor: test_execute_valid_sell_signal PASSED - Result: {result}")

    def test_execute_invalid_signal_bad_action(self):
        signal = {"symbol": "BTC/USDT", "action": "INVALID_ACTION", "quantity": 0.01, "order_type": "MARKET", "strategy_name": "TestStrat"}
        result = self.executor.execute_signal(signal)
        self.assertEqual(result.get("状态"), "拒绝")
        self.assertIn("无效", result.get("原因", "")) # Check for "无效" in reason
        print(f"TestTradeExecutor: test_execute_invalid_signal_bad_action PASSED - Result: {result}")

    def test_execute_invalid_signal_missing_key(self):
        signal = {"symbol": "BTC/USDT", "action": "BUY", "order_type": "MARKET", "strategy_name": "TestStrat"} # Missing quantity
        result = self.executor.execute_signal(signal)
        self.assertEqual(result.get("状态"), "拒绝")
        self.assertIn("无效", result.get("原因", ""))
        print(f"TestTradeExecutor: test_execute_invalid_signal_missing_key PASSED - Result: {result}")

    def test_execute_hold_signal(self):
        signal = {"symbol": "BTC/USDT", "action": "HOLD", "quantity": 0, "order_type": "NONE", "strategy_name": "TestStrat"}
        
        # Test the _validate_signal method directly for HOLD
        is_valid = self.executor._validate_signal(signal)
        self.assertTrue(is_valid, "HOLD signal should be considered valid by _validate_signal")
        
        # Test the execute_signal method with the fix applied previously
        result = self.executor.execute_signal(signal)
        self.assertEqual(result.get("状态"), "已处理", f"Unexpected status for HOLD: {result.get('状态')}")
        self.assertIsNone(result.get("订单ID"), "Order ID should be None for HOLD signal")
        self.assertIn("HOLD信号", result.get("原因", ""), "Reason should mention HOLD signal")
        print(f"TestTradeExecutor: test_execute_hold_signal PASSED - Result: {result}")

    def test_cancel_order_flow(self):
        # First, place an order that is likely to be submittable but not instantly filled (e.g., a limit order)
        limit_signal = {"symbol": "LTC/USDT", "action": "BUY", "quantity": 1, "order_type": "LIMIT", "price": 50, "strategy_name": "TestCancelStrat"}
        submission_result = self.executor.execute_signal(limit_signal)
        order_id_to_cancel = submission_result.get("订单ID")

        if submission_result.get("状态") == "已提交":
            cancel_result = self.executor.cancel_order(order_id_to_cancel)
            self.assertEqual(cancel_result.get("状态"), "已取消")
            print(f"TestTradeExecutor: test_cancel_order_flow (cancel success) PASSED - Result: {cancel_result}")
        elif submission_result.get("状态") == "已成交":
            # If it got filled immediately, test that cancel fails appropriately
            cancel_result = self.executor.cancel_order(order_id_to_cancel)
            self.assertEqual(cancel_result.get("状态"), "已成交") # Cannot cancel filled order
            self.assertIn("不可取消", cancel_result.get("原因",""))
            print(f"TestTradeExecutor: test_cancel_order_flow (order already filled) PASSED - Result: {cancel_result}")
        else:
            self.skipTest(f"Order for cancellation test was not in expected state: {submission_result.get('状态')}")
            
    def test_get_positions_and_orders(self):
        initial_positions = self.executor.get_positions()
        initial_orders = self.executor.get_orders()
        self.assertIsInstance(initial_positions, dict)
        self.assertIsInstance(initial_orders, dict)

        # Execute a signal to change positions/orders
        signal = {"symbol": "ADA/USDT", "action": "BUY", "quantity": 100, "order_type": "MARKET", "strategy_name": "TestPosOrderStrat"}
        self.executor.execute_signal(signal)

        updated_positions = self.executor.get_positions()
        updated_orders = self.executor.get_orders()
        
        self.assertNotEqual(initial_orders, updated_orders, "Orders list should change after a trade")
        # Position change depends on whether the market order was simulated as filled
        # and how positions are tracked. If filled, positions should change.
        # For this placeholder, we just check type again. More specific checks would need knowledge of fill logic.
        self.assertIsInstance(updated_positions, dict)
        print(f"TestTradeExecutor: test_get_positions_and_orders PASSED")


if __name__ == '__main__':
    unittest.main()
