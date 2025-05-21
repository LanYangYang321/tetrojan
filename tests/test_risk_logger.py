import unittest
from trading_bot import risk_logger

class TestRiskLogger(unittest.TestCase):
    def test_logger_instance(self):
        self.assertIsNotNone(risk_logger.BOT_LOGGER)
        risk_logger.BOT_LOGGER.info("Test log message from test_risk_logger.")
        print("TestRiskLogger: test_logger_instance PASSED (check log output)")

    def test_risk_functions_run(self):
        # Just basic execution checks, not for correctness of logic here
        risk_configs = {"max_order_sizes": {"TEST/USDT": 1, "default": 0.5}, "max_total_exposure_usd": 1000}
        self.assertTrue(risk_logger.check_max_order_size("TEST/USDT", 0.5, risk_configs["max_order_sizes"]))
        self.assertFalse(risk_logger.check_max_order_size("TEST/USDT", 1.5, risk_configs["max_order_sizes"]))
        
        mock_positions = {"TEST/USDT": {"value_usd": 500}}
        self.assertTrue(risk_logger.check_overall_portfolio_exposure(mock_positions, risk_configs["max_total_exposure_usd"]))
        
        risk_logger.handle_exchange_error({"code": -1, "msg": "test error"})
        print("TestRiskLogger: test_risk_functions_run PASSED")

if __name__ == '__main__':
    unittest.main()
