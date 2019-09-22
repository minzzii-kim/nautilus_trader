# -------------------------------------------------------------------------------------------------
# <copyright file="test_backtest_execution.py" company="Nautech Systems Pty Ltd">
#  Copyright (C) 2015-2019 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  https://nautechsystems.io
# </copyright>
# -------------------------------------------------------------------------------------------------

import pandas as pd
import unittest

from nautilus_trader.common.brokerage import CommissionCalculator
from nautilus_trader.common.data import DataClient
from nautilus_trader.common.clock import TestClock
from nautilus_trader.common.guid import TestGuidFactory
from nautilus_trader.common.portfolio import Portfolio
from nautilus_trader.common.performance import PerformanceAnalyzer
from nautilus_trader.common.logger import TestLogger
from nautilus_trader.common.execution import InMemoryExecutionDatabase, ExecutionEngine
from nautilus_trader.model.enums import OrderSide, Currency, AccountType
from nautilus_trader.model.objects import Quantity, Price, Money
from nautilus_trader.model.events import OrderRejected, OrderWorking, OrderModified, OrderFilled
from nautilus_trader.model.identifiers import TraderId, AccountId, Venue
from nautilus_trader.trade.strategy import TradingStrategy
from nautilus_trader.backtest.execution import BacktestExecClient
from nautilus_trader.backtest.models import FillModel
from test_kit.strategies import TestStrategy1
from test_kit.data import TestDataProvider
from test_kit.stubs import TestStubs

UNIX_EPOCH = TestStubs.unix_epoch()
USDJPY_FXCM = TestStubs.symbol_usdjpy_fxcm()


class BacktestExecClientTests(unittest.TestCase):

    def setUp(self):
        # Fixture Setup
        self.usdjpy = TestStubs.instrument_usdjpy()
        self.bid_data_1min = TestDataProvider.usdjpy_1min_bid()[:2000]
        self.ask_data_1min = TestDataProvider.usdjpy_1min_ask()[:2000]

        self.instruments = [self.usdjpy]
        self.data_ticks = {self.usdjpy.symbol: pd.DataFrame()}
        self.data_bars_bid = {self.usdjpy.symbol: self.bid_data_1min}
        self.data_bars_ask = {self.usdjpy.symbol: self.ask_data_1min}

        self.strategies = [TestStrategy1(TestStubs.bartype_usdjpy_1min_bid())]

        self.clock = TestClock()
        self.guid_factory = TestGuidFactory()
        self.logger = TestLogger()

        self.data_client = DataClient(
            venue=Venue('FXCM'),
            clock=self.clock,
            guid_factory=self.guid_factory,
            logger=self.logger)

        self.portfolio = Portfolio(
            clock=self.clock,
            guid_factory=self.guid_factory,
            logger=self.logger)

        self.analyzer = PerformanceAnalyzer()

        trader_id = TraderId('TESTER', '000')
        account_id = TestStubs.account_id()

        self.exec_db = InMemoryExecutionDatabase(
            trader_id=trader_id,
            logger=self.logger)
        self.exec_engine = ExecutionEngine(
            trader_id=trader_id,
            account_id=account_id,
            database=self.exec_db,
            portfolio=self.portfolio,
            analyzer=self.analyzer,
            clock=self.clock,
            guid_factory=self.guid_factory,
            logger=self.logger)

        self.exec_client = BacktestExecClient(
            self.exec_engine,
            instruments=self.instruments,
            frozen_account=False,
            starting_capital=Money(1000000),
            account_currency=Currency.USD,
            fill_model=FillModel(),
            commission_calculator=CommissionCalculator(),
            portfolio=self.portfolio,
            clock=TestClock(),
            guid_factory=TestGuidFactory(),
            logger=TestLogger())
        self.exec_engine.register_client(self.exec_client)

    def test_can_send_collateral_inquiry(self):
        pass
        # Arrange
        strategy = TradingStrategy(order_id_tag='001')
        self.exec_engine.register_strategy(strategy)

        # Act
        strategy.account_inquiry()

        # Assert
        # self.assertEqual(2, strategy.account.event_count)

    def test_can_submit_market_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        order = strategy.order_factory.market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000))

        # Act
        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Assert
        self.assertEqual(5, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[3], OrderFilled))
        self.assertEqual(Price('90.003'), strategy.order(order.id).average_price)

    def test_can_submit_limit_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        order = strategy.order_factory.limit(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('80.000'))

        # Act
        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Assert
        self.assertEqual(4, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[3], OrderWorking))
        self.assertEqual(Price('80.000'), order.price)

    def test_can_submit_atomic_market_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        atomic_order = strategy.order_factory.atomic_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('80.000'))

        # Act
        strategy.submit_atomic_order(atomic_order, strategy.position_id_generator.generate())

        # Assert
        # print(strategy.object_storer.get_store())
        self.assertEqual(7, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[3], OrderFilled))
        self.assertEqual(Price('80.000'), atomic_order.stop_loss.price)
        self.assertTrue(atomic_order.stop_loss.id not in self.exec_client.atomic_child_orders)

    def test_can_submit_atomic_stop_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        atomic_order = strategy.order_factory.atomic_stop_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('97.000'),
            Price('96.710'),
            Price('86.000'))

        # Act
        strategy.submit_atomic_order(atomic_order, strategy.position_id_generator.generate())

        # Assert
        # print(strategy.object_storer.get_store())
        self.assertEqual(4, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[3], OrderWorking))
        self.assertTrue(atomic_order.entry.id in self.exec_client.atomic_child_orders)
        self.assertTrue(atomic_order.stop_loss in self.exec_client.atomic_child_orders[atomic_order.entry.id])
        self.assertTrue(atomic_order.take_profit in self.exec_client.atomic_child_orders[atomic_order.entry.id])

    def test_can_modify_stop_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        order = strategy.order_factory.stop_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('96.711'))

        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Act
        strategy.modify_order(order, Price('96.714'))

        # Assert
        self.assertEqual(Price('96.714'), strategy.order(order.id).price)
        self.assertEqual(5, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[4], OrderModified))

    def test_can_modify_atomic_order_working_stop_loss(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        atomic_order = strategy.order_factory.atomic_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('85.000'))

        strategy.submit_atomic_order(atomic_order, strategy.position_id_generator.generate())

        # Act
        strategy.modify_order(atomic_order.stop_loss, Price('85.100'))

        # Assert
        self.assertEqual(Price('85.100'), strategy.order(atomic_order.stop_loss.id).price)
        self.assertEqual(8, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[7], OrderModified))

    def test_submit_market_order_with_slippage_fill_model_slips_order(self):
        # Arrange
        fill_model = FillModel(
            prob_fill_at_limit=0.0,
            prob_fill_at_stop=1.0,
            prob_slippage=1.0,
            random_seed=None)

        exec_client = BacktestExecClient(
            exec_engine=self.exec_engine,
            instruments=self.instruments,
            frozen_account=False,
            starting_capital=Money(1000000),
            account_currency=Currency.USD,
            fill_model=fill_model,
            commission_calculator=CommissionCalculator(),
            portfolio=self.portfolio,
            clock=TestClock(),
            guid_factory=TestGuidFactory(),
            logger=TestLogger())

        self.exec_engine.register_client(exec_client)
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        order = strategy.order_factory.market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000))

        # Act
        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Assert
        self.assertEqual(5, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[3], OrderFilled))
        self.assertEqual(Price('90.004'), strategy.order(order.id).average_price)

    def test_submit_order_with_no_market_rejects_order(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        order = strategy.order_factory.stop_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('80.000'))

        # Act
        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Assert
        self.assertEqual(3, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[2], OrderRejected))

    def test_submit_order_with_invalid_price_gets_rejected(self):
        # Arrange
        strategy = TestStrategy1(bar_type=TestStubs.bartype_usdjpy_1min_bid())
        self.data_client.register_strategy(strategy)
        self.exec_engine.register_strategy(strategy)
        strategy.start()

        bar = TestStubs.bar_3decimal()
        self.exec_client.process_bars(self.usdjpy.symbol, bar, bar)  # Prepare market
        order = strategy.order_factory.stop_market(
            USDJPY_FXCM,
            OrderSide.BUY,
            Quantity(100000),
            Price('80.000'))

        # Act
        strategy.submit_order(order, strategy.position_id_generator.generate())

        # Assert
        self.assertEqual(3, strategy.object_storer.count)
        self.assertTrue(isinstance(strategy.object_storer.get_store()[2], OrderRejected))
