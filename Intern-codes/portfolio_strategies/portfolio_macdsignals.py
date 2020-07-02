from typing import List, Dict
from vnpy.trader.constant import Interval
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


class MACDSignals(StrategyTemplate):
    """"""

    author = "yiran"

    fast_period = 12
    slow_period = 26
    signal_period = 9
    trailing_percent = 0.8
    fixed_size = 1
    bar_interval = 20
    bar_frequency = Interval.MINUTE



    intra_trade_high = 0
    intra_trade_low = 0



    parameters = [
        "fast_period",
        "slow_period",
        'signal_period',
        "trailing_percent",
        "fixed_size"
    ]
    variables = [
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
            self.signals[vt_symbol] = MACDSignal(self,vt_symbol)




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




class MACDSignal:
    """"""

    def __init__(self, strategy:StrategyTemplate, vt_symbol:str):
        """"""

        self.portfolio= strategy
        self.vt_symbol = vt_symbol



        self.fast_period = self.portfolio.fast_period
        self.slow_period = self.portfolio.slow_period
        self.signal_period = self.portfolio.signal_period
        self.trailing_percent= self.portfolio.trailing_percent
        self.fixed_size= self.portfolio.fixed_size
        self.bar_interval = self.portfolio.bar_interval
        self.bar_frequency = self.portfolio.bar_frequency

        self.macd_value = 0
        self.intra_trade_high = 0
        self.intra_trade_low = 0



        self.bg = BarGenerator(self.on_bar, self.bar_interval, self.on_5min_bar,self.bar_frequency)
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
        macd,macd_signal,_ = am.macd(self.fast_period, self.slow_period, self.signal_period,array=True)

        long_trend = (macd[-2] < macd_signal[-2]) and (macd[-1] > macd_signal[-1])
        short_trend = (macd[-2] > macd_signal[-2]) and (macd[-1] < macd_signal[-1])


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
