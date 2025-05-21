import unittest
from trading_bot import strategy_scheduler
from trading_bot import strategy_library
from trading_bot.config import get_strategy_configs

class TestStrategyScheduler(unittest.TestCase):
    def test_choose_strategy(self):
        configs = get_strategy_configs()
        
        trend_state = {"market_state": "Trend", "confidence": 0.8}
        strategy_trend = strategy_scheduler.choose_strategy(trend_state, configs)
        self.assertIsInstance(strategy_trend, strategy_library.MovingAverageCrossoverStrategy) # Based on current scheduler logic

        range_state = {"market_state": "Range", "confidence": 0.7}
        strategy_range = strategy_scheduler.choose_strategy(range_state, configs)
        self.assertIsInstance(strategy_range, strategy_library.BollingerBandsMeanReversionStrategy) # Based on current scheduler logic
        
        unknown_state = {"market_state": "Unknown", "confidence": 0.5}
        strategy_unknown = strategy_scheduler.choose_strategy(unknown_state, configs)
        self.assertIsNone(strategy_unknown)
        print("TestStrategyScheduler: test_choose_strategy PASSED")

if __name__ == '__main__':
    unittest.main()
