from typing import List, Dict

from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.trader.object import TickData, BarData
from vnpy.app.cta_strategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    TargetPosTemplate
)


class TredningFollowingSignals(StrategyTemplate):
    """"""

    author = "yiran"

    atr_window = 22
    atr_ma_window = 10
    rsi_window = 5
    rsi_entry = 16
    trailing_percent = 0.8
    fixed_size = 1

    atr_value = 0
    atr_ma = 0
    rsi_value = 0
    rsi_buy = 0
    rsi_sell = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
        "atr_window",
        "atr_ma_window",
        "rsi_window",
        "rsi_entry",
        "trailing_percent",
        "fixed_size"
    ]
    variables = [
        "atr_value",
        "atr_ma",
        "rsi_value",
        "rsi_buy",
        "rsi_sell"
    ]

    def __init__(
        self,
        strategy_engine: StrategyEngine,
        strategy_name: str,
        vt_symbols: List[str],
        setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)

        self.signals = {}
        for vt_symbol in self.vt_symbols:
            self.signals[vt_symbol] = TredningFollowingSignal(self,vt_symbol)




    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_buy = 50 + self.rsi_entry
        self.rsi_sell = 50 - self.rsi_entry

        self.load_bars(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")


    def on_bars(self, bars: Dict[str, BarData]):
        """"""
        for vt_symbol in bars:
            self.signals[vt_symbol].on_bar(bars[vt_symbol])




class TredningFollowingSignal:
    """"""

    def __init__(self, strategy:StrategyTemplate, vt_symbol:str):
        """"""

        self.portfolio= strategy
        self.vt_symbol = vt_symbol


        self.atr_window = self.portfolio.atr_window
        self.atr_ma_window = self.portfolio.atr_ma_window
        self.rsi_window = self.portfolio.rsi_window
        self.rsi_entry = self.portfolio.rsi_entry
        self.trailing_percent= self.portfolio.trailing_percent
        self.fixed_size= self.portfolio.fixed_size

        self.atr_value = 0
        self.atr_ma = 0
        self.rsi_value = 0
        self.rsi_buy = 50 + self.rsi_entry
        self.rsi_sell = 50 - self.rsi_entry
        self.intra_trade_high = 0
        self.intra_trade_low = 0


        self.limit_orders = []
        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)

        if not self.am.inited:
            return


        self.portfolio.cancel_all()
        am = self.am
        atr_array = am.atr(self.atr_window, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_window:].mean()
        self.rsi_value = am.rsi(self.rsi_window)

        symbol_pos = self.portfolio.get_pos(self.vt_symbol)
        if symbol_pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_buy:
                    open_order = self.portfolio.buy(self.vt_symbol, bar.close_price+5,self.fixed_size)
                    self.limit_orders.append(open_order)
                elif self.rsi_value < self.rsi_sell:
                    open_order = self.portfolio.short(self.vt_symbol, bar.close_price-5,self.fixed_size)
        elif symbol_pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent / 100)
            if bar.close_price <= long_stop:
                close_order = self.portfolio.sell(self.vt_symbol, bar.close_price - 5, abs(symbol_pos))
                self.limit_orders.append(close_order)
        elif symbol_pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * (1 + self.trailing_percent / 100)
            if bar.close_price >= short_stop:
                close_order = self.portfolio.cover(self.vt_symbol, bar.high_price + 5, abs(symbol_pos))
                self.limit_orders.append(close_order)
