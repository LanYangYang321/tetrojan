import unittest
import pandas as pd
from trading_bot import strategy_library
from trading_bot.data_collector import fetch_mock_ohlcv_data


class TestStrategyLibrary(unittest.TestCase):
    def test_base_strategy_creation(self):
        # Test creating an instance of each concrete strategy
        strategies = [
            strategy_library.MovingAverageCrossoverStrategy,
            strategy_library.ChannelBreakoutStrategy,
            strategy_library.BollingerBandsMeanReversionStrategy,
            strategy_library.GridTradingStrategy
        ]
        mock_data = fetch_mock_ohlcv_data("TEST/USDT", limit=5)

        for strategy_class in strategies:
            strategy_instance = strategy_class(config={"test_param": 123})
            self.assertIsInstance(strategy_instance, strategy_library.BaseStrategy)
            self.assertIn("test_param", strategy_instance.get_config())
            # Test generate_signals (placeholder)
            signals = strategy_instance.generate_signals(mock_data)
            self.assertIsInstance(signals, pd.DataFrame) # Expecting empty DataFrame for now
            print(f"TestStrategyLibrary: Tested {strategy_class.__name__}")
        
        print("TestStrategyLibrary: All strategies tested.")

if __name__ == '__main__':
    unittest.main()
