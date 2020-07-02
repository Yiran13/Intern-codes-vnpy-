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


class MASignals(StrategyTemplate):
    """"""

    author = "yiran"

    long_ma_window = 22
    short_ma_window = 10
    trailing_percent = 0.8
    fixed_size = 1


    intra_trade_high = 0
    intra_trade_low = 0

    long_ma_value = 0
    short_ma_value = 0

    parameters = [
        "long_ma_window",
        "short_ma_window",
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
            self.signals[vt_symbol] = MASignal(self,vt_symbol)




    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

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




class MASignal:
    """"""

    def __init__(self, strategy:StrategyTemplate, vt_symbol:str):
        """"""

        self.portfolio= strategy
        self.vt_symbol = vt_symbol


        self.long_ma_window = self.portfolio.long_ma_window
        self.short_ma_window = self.portfolio.short_ma_window
        self.trailing_percent= self.portfolio.trailing_percent
        self.fixed_size= self.portfolio.fixed_size

        self.long_ma_value = 0
        self.short_ma_value = 0
        self.intra_trade_high = 0
        self.intra_trade_low = 0



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
        long_ma_array = am.sma(self.long_ma_window, array=True)
        short_ma_array = am.sma(self.short_ma_window, array=True)
        long_trend = (long_ma_array[-2] > short_ma_array[-2]) and (long_ma_array[-1] < short_ma_array[-1])
        short_trend = (long_ma_array[-2] < short_ma_array[-2]) and (long_ma_array[-1] > short_ma_array[-1])


        symbol_pos = self.portfolio.get_pos(self.vt_symbol)
        if symbol_pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if long_trend:

                open_order = self.portfolio.buy(self.vt_symbol, bar.close_price+5,self.fixed_size)

            elif short_trend:

                open_order = self.portfolio.short(self.vt_symbol, bar.close_price-5,self.fixed_size)

        elif symbol_pos > 0:

            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent / 100)
            # if bar.close_price <= long_stop:
            #     close_order = self.portfolio.sell(self.vt_symbol, bar.close_price - 5, abs(symbol_pos))
            #     self.limit_orders.append(close_order)
            if short_trend:

                close_order = self.portfolio.sell(self.vt_symbol, bar.close_price - 5, abs(symbol_pos))


        elif symbol_pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * (1 + self.trailing_percent / 100)
            # if bar.close_price >= short_stop:
            #     close_order = self.portfolio.cover(self.vt_symbol, bar.high_price + 5, abs(symbol_pos))
            #     self.limit_orders.append(close_order)
            if long_trend:
                close_order = self.portfolio.cover(self.vt_symbol, bar.high_price + 5, abs(symbol_pos))
