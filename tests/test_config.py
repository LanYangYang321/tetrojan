import unittest
from trading_bot import config

class TestConfig(unittest.TestCase):
    def test_configs_loadable(self):
        self.assertIsNotNone(config.get_main_loop_config())
        self.assertIsNotNone(config.get_strategy_configs())
        self.assertIsNotNone(config.get_trade_executor_config())
        self.assertIsNotNone(config.get_risk_configs())
        print("TestConfig: test_configs_loadable PASSED")

if __name__ == '__main__':
    unittest.main()
