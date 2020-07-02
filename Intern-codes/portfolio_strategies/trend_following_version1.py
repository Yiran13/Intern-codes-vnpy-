from typing import List, Dict

from vnpy.app.portfolio_strategy import StrategyTemplate, StrategyEngine
from vnpy.trader.utility import BarGenerator, ArrayManager
from vnpy.trader.object import TickData, BarData



class ATR_RSI_Strategy(StrategyTemplate):
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
        self.bgs: Dict[str, BarGenerator] = {}
        self.ams: Dict[str, ArrayManager] = {}
        self.intra_trade_lows: Dict[str, float] = {}
        self.intra_trade_highs: Dict[str, float] = {}
        self.atr_values: Dict[str, float] = {}
        self.atr_mas: Dict[str, float] = {}
        self.rsi_values: Dict[str, float] = {}

        def on_bar(bar: BarData):



            """"""
            pass
        self.bgs[self.vt_symbols[0]] = BarGenerator(on_bar,15,self.on_15min_symbol_bar1)
        self.bgs[self.vt_symbols[1]] = BarGenerator(on_bar,15,self.on_15min_symbol_bar2)
        # self.bgs[self.vt_symbols[2]] = BarGenerator(on_bar,15,self.on_15min_symbol_bar3)

        self.ams[self.vt_symbols[0]] = ArrayManager()
        self.ams[self.vt_symbols[1]] = ArrayManager()
        # self.ams[self.vt_symbols[2]] = ArrayManager()

        self.intra_trade_lows[self.vt_symbols[0]] = 0
        self.intra_trade_lows[self.vt_symbols[1]] = 0
        # self.intra_trade_lows[self.vt_symbols[2]] = 0

        self.intra_trade_highs[self.vt_symbols[0]] = 0
        self.intra_trade_highs[self.vt_symbols[1]] = 0
        # self.intra_trade_highs[self.vt_symbols[2]] = 0

        self.atr_values[self.vt_symbols[0]] = 0
        self.atr_values[self.vt_symbols[1]] = 0
        # self.atr_values[self.vt_symbols[2]] = 0

        self.atr_mas[self.vt_symbols[0]] = 0
        self.atr_mas[self.vt_symbols[1]] = 0
        # self.atr_mas[self.vt_symbols[2]] = 0

        self.rsi_values[self.vt_symbols[0]] = 0
        self.rsi_values[self.vt_symbols[1]] = 0
        # self.rsi_values[self.vt_symbols[2]] = 0

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


    def on_15min_symbol_bar1(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        vt_symbol = self.vt_symbols[0]
        am = self.ams[vt_symbol]
        am.update_bar(bar)
        if not am.inited:
            return
        symbol_pos = self.get_pos(vt_symbol)

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_values[vt_symbol] = atr_array[-1]
        self.atr_mas[vt_symbol] = atr_array[-self.atr_ma_window:].mean()
        self.rsi_values[vt_symbol] = am.rsi(self.rsi_window)

        if symbol_pos == 0:
            self.intra_trade_highs[vt_symbol] = bar.high_price
            self.intra_trade_lows[vt_symbol] = bar.low_price

            if self.atr_values[vt_symbol] > self.atr_mas[vt_symbol]:
                if self.rsi_values[vt_symbol] > self.rsi_buy:
                    self.buy(vt_symbol, bar.close_price + 5, self.fixed_size)
                elif self.rsi_values[vt_symbol] < self.rsi_sell:
                    self.short(vt_symbol, bar.close_price - 5, self.fixed_size)

        elif symbol_pos > 0:
            self.intra_trade_highs[vt_symbol] = max(self.intra_trade_highs[vt_symbol], bar.high_price)
            self.intra_trade_lows[vt_symbol] = bar.low_price

            long_stop = self.intra_trade_highs[vt_symbol] * (1 - self.trailing_percent / 100)

            if bar.close_price <= long_stop:
                self.sell(vt_symbol, bar.close_price - 5, abs(symbol_pos))

        elif symbol_pos < 0:
            self.intra_trade_lows[vt_symbol] = min(self.intra_trade_lows[vt_symbol], bar.low_price)
            self.intra_trade_highs[vt_symbol] = bar.high_price

            short_stop = self.intra_trade_lows[vt_symbol] * (1 + self.trailing_percent / 100)

            if bar.close_price >= short_stop:
                self.cover(vt_symbol, bar.close_price + 5, abs(symbol_pos))



    def on_15min_symbol_bar2(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        vt_symbol = self.vt_symbols[1]
        am = self.ams[vt_symbol]
        am.update_bar(bar)
        if not am.inited:
            return
        symbol_pos = self.get_pos(vt_symbol)

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_values[vt_symbol] = atr_array[-1]
        self.atr_mas[vt_symbol] = atr_array[-self.atr_ma_window:].mean()
        self.rsi_values[vt_symbol] = am.rsi(self.rsi_window)

        if symbol_pos == 0:
            self.intra_trade_highs[vt_symbol] = bar.high_price
            self.intra_trade_lows[vt_symbol] = bar.low_price

            if self.atr_values[vt_symbol] > self.atr_mas[vt_symbol]:
                if self.rsi_values[vt_symbol] > self.rsi_buy:
                    self.buy(vt_symbol, bar.close_price + 5, self.fixed_size)
                elif self.rsi_values[vt_symbol] < self.rsi_sell:
                    self.short(vt_symbol, bar.close_price - 5, self.fixed_size)

        elif symbol_pos > 0:
            self.intra_trade_highs[vt_symbol] = max(self.intra_trade_highs[vt_symbol], bar.high_price)
            self.intra_trade_lows[vt_symbol] = bar.low_price

            long_stop = self.intra_trade_highs[vt_symbol] * (1 - self.trailing_percent / 100)

            if bar.close_price <= long_stop:
                self.sell(vt_symbol, bar.close_price - 5, abs(symbol_pos))

        elif symbol_pos < 0:
            self.intra_trade_lows[vt_symbol] = min(self.intra_trade_lows[vt_symbol], bar.low_price)
            self.intra_trade_highs[vt_symbol] = bar.high_price

            short_stop = self.intra_trade_lows[vt_symbol] * (1 + self.trailing_percent / 100)

            if bar.close_price >= short_stop:
                self.cover(vt_symbol, bar.close_price + 5, abs(symbol_pos))


    def on_15min_symbol_bar3(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        vt_symbol = self.vt_symbols[2]
        am = self.ams[vt_symbol]
        am.update_bar(bar)
        if not am.inited:
            return
        symbol_pos = self.get_pos(vt_symbol)

        atr_array = am.atr(self.atr_window, array=True)
        self.atr_values[vt_symbol] = atr_array[-1]
        self.atr_mas[vt_symbol] = atr_array[-self.atr_ma_window:].mean()
        self.rsi_values[vt_symbol] = am.rsi(self.rsi_window)

        if symbol_pos == 0:
            self.intra_trade_highs[vt_symbol] = bar.high_price
            self.intra_trade_lows[vt_symbol] = bar.low_price

            if self.atr_values[vt_symbol] > self.atr_mas[vt_symbol]:
                if self.rsi_values[vt_symbol] > self.rsi_buy:
                    self.buy(vt_symbol, bar.close_price + 5, self.fixed_size)
                elif self.rsi_values[vt_symbol] < self.rsi_sell:
                    self.short(vt_symbol, bar.close_price - 5, self.fixed_size)

        elif symbol_pos > 0:
            self.intra_trade_highs[vt_symbol] = max(self.intra_trade_highs[vt_symbol], bar.high_price)
            self.intra_trade_lows[vt_symbol] = bar.low_price

            long_stop = self.intra_trade_highs[vt_symbol] * (1 - self.trailing_percent / 100)

            if bar.close_price <= long_stop:
                self.sell(vt_symbol, bar.close_price - 5, abs(symbol_pos))

        elif symbol_pos < 0:
            self.intra_trade_lows[vt_symbol] = min(self.intra_trade_lows[vt_symbol], bar.low_price)
            self.intra_trade_highs[vt_symbol] = bar.high_price

            short_stop = self.intra_trade_lows[vt_symbol] * (1 + self.trailing_percent / 100)

            if bar.close_price >= short_stop:
                self.cover(vt_symbol, bar.close_price + 5, abs(symbol_pos))

    def on_bars(self, bars: Dict[str, BarData]):
        """"""
        for vt_symbol in bars:
            symbol_bg = self.bgs[vt_symbol]
            symbol_bar = bars[vt_symbol]
            symbol_bg.update_bar(symbol_bar)
