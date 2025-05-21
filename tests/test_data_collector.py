import unittest
import pandas as pd
from trading_bot import data_collector

class TestDataCollector(unittest.TestCase):
    def test_fetch_mock_data(self):
        df = data_collector.fetch_mock_ohlcv_data("BTC/USDT", limit=10)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 10)
        self.assertListEqual(list(df.columns), ['open', 'high', 'low', 'close', 'volume'])
        print("TestDataCollector: test_fetch_mock_data PASSED")

if __name__ == '__main__':
    unittest.main()
