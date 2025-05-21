# This file will contain the StrategyLibrary class.
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    策略基类，定义所有交易策略的通用接口。
    """
    def __init__(self, strategy_name: str, config: dict = None):
        self.strategy_name = strategy_name
        self.config = config if config is not None else {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self):
        """
        验证策略配置参数是否有效。
        """
        pass

    @abstractmethod
    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        根据市场数据生成交易信号。
        """
        pass

    def update_config(self, new_config: dict):
        self.config.update(new_config)
        self._validate_config()
        print(f"策略 [{self.strategy_name}] 配置已更新: {self.config}")

    def get_config(self) -> dict:
        return self.config

    def __str__(self) -> str:
        return f"策略名称: {self.strategy_name}, 配置: {self.config}"

class MovingAverageCrossoverStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        super().__init__("MovingAverageCrossover", config)

    def _validate_config(self):
        # Placeholder: Add specific validation later
        pass

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        # Placeholder: Implement actual signal generation later
        print(f"[{self.strategy_name}] generating signals with data:\n{market_data.head()}")
        # Example: signals_df = pd.DataFrame(index=market_data.index)
        # signals_df['signal'] = 0 # 0: hold, 1: buy, -1: sell
        return pd.DataFrame()

class ChannelBreakoutStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        super().__init__("ChannelBreakout", config)

    def _validate_config(self):
        # Placeholder: Add specific validation later
        pass

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        # Placeholder: Implement actual signal generation later
        print(f"[{self.strategy_name}] generating signals with data:\n{market_data.head()}")
        return pd.DataFrame()

class BollingerBandsMeanReversionStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        super().__init__("BollingerBandsMeanReversion", config)

    def _validate_config(self):
        # Placeholder: Add specific validation later
        pass

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        # Placeholder: Implement actual signal generation later
        print(f"[{self.strategy_name}] generating signals with data:\n{market_data.head()}")
        return pd.DataFrame()

class GridTradingStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        super().__init__("GridTrading", config)

    def _validate_config(self):
        # Placeholder: Add specific validation later
        pass

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        # Placeholder: Implement actual signal generation later
        print(f"[{self.strategy_name}] generating signals with data:\n{market_data.head()}")
        return pd.DataFrame()
