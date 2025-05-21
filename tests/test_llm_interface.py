import unittest
import pandas as pd
from trading_bot import llm_interface
from trading_bot.data_collector import fetch_mock_ohlcv_data


class TestLlmInterface(unittest.TestCase):
    def test_get_market_state(self):
        mock_data = fetch_mock_ohlcv_data("TEST/USDT")
        state = llm_interface.get_market_state(mock_data)
        self.assertIn("market_state", state)
        self.assertIn("confidence", state)
        self.assertIn(state["market_state"], ["Trend", "Range"])
        print("TestLlmInterface: test_get_market_state PASSED")

if __name__ == '__main__':
    unittest.main()
