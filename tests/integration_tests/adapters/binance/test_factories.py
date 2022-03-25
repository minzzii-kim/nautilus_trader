# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2022 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

import asyncio

import pytest

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
from nautilus_trader.adapters.binance.config import BinanceExecClientConfig
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance.factories import BinanceLiveExecClientFactory
from nautilus_trader.adapters.binance.factories import _get_http_base_url
from nautilus_trader.adapters.binance.factories import _get_ws_base_url
from nautilus_trader.adapters.binance.futures.data import BinanceFuturesDataClient
from nautilus_trader.adapters.binance.futures.execution import BinanceFuturesExecutionClient
from nautilus_trader.adapters.binance.spot.data import BinanceSpotDataClient
from nautilus_trader.adapters.binance.spot.execution import BinanceSpotExecutionClient
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.logging import LiveLogger
from nautilus_trader.common.logging import LogLevel
from nautilus_trader.msgbus.bus import MessageBus
from tests.test_kit.mocks.cache_database import MockCacheDatabase
from tests.test_kit.stubs.identifiers import TestIdStubs


class TestBinanceFactories:
    def setup(self):
        # Fixture Setup
        self.loop = asyncio.get_event_loop()
        self.clock = LiveClock()
        self.logger = LiveLogger(
            loop=self.loop,
            clock=self.clock,
            level_stdout=LogLevel.DEBUG,
        )

        self.trader_id = TestIdStubs.trader_id()
        self.strategy_id = TestIdStubs.strategy_id()
        self.account_id = TestIdStubs.account_id()

        self.msgbus = MessageBus(
            trader_id=self.trader_id,
            clock=self.clock,
            logger=self.logger,
        )

        self.cache_db = MockCacheDatabase(
            logger=self.logger,
        )

        self.cache = Cache(
            database=self.cache_db,
            logger=self.logger,
        )

    @pytest.mark.parametrize(
        "config, expected",
        [
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=False,
                    testnet=False,
                ),
                "https://api.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=False,
                    testnet=False,
                ),
                "https://sapi.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=False,
                    testnet=False,
                ),
                "https://fapi.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_COIN,
                    us=False,
                    testnet=False,
                ),
                "https://dapi.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=True,
                    testnet=False,
                ),
                "https://api.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=True,
                    testnet=False,
                ),
                "https://sapi.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=True,
                    testnet=False,
                ),
                "https://fapi.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_COIN,
                    us=True,
                    testnet=False,
                ),
                "https://dapi.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=False,
                    testnet=True,
                ),
                "https://testnet.binance.vision/api",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=False,
                    testnet=True,
                ),
                "https://testnet.binance.vision/api",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=False,
                    testnet=True,
                ),
                "https://testnet.binancefuture.com",
            ],
        ],
    )
    def test_get_http_base_url(self, config, expected):
        # Arrange, Act
        base_url = _get_http_base_url(config)

        # Assert
        assert base_url == expected

    @pytest.mark.parametrize(
        "config, expected",
        [
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=False,
                    testnet=False,
                ),
                "wss://stream.binance.com:9443",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=False,
                    testnet=False,
                ),
                "wss://stream.binance.com:9443",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=False,
                    testnet=False,
                ),
                "wss://fstream-auth.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_COIN,
                    us=False,
                    testnet=False,
                ),
                "wss://dstream.binance.com",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=True,
                    testnet=False,
                ),
                "wss://stream.binance.us:9443",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=True,
                    testnet=False,
                ),
                "wss://stream.binance.us:9443",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=True,
                    testnet=False,
                ),
                "wss://fstream-auth.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_COIN,
                    us=True,
                    testnet=False,
                ),
                "wss://dstream.binance.us",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.SPOT,
                    us=False,
                    testnet=True,
                ),
                "wss://testnet.binance.vision",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.MARGIN,
                    us=False,
                    testnet=True,
                ),
                "wss://testnet.binance.vision",
            ],
            [
                BinanceExecClientConfig(
                    account_type=BinanceAccountType.FUTURES_USDT,
                    us=False,
                    testnet=True,
                ),
                "wss://stream.binancefuture.com",
            ],
        ],
    )
    def test_get_ws_base_url(self, config, expected):
        # Arrange, Act
        base_url = _get_ws_base_url(config)

        # Assert
        assert base_url == expected

    def test_create_binance_live_spot_data_client(self, binance_http_client):
        # Arrange, Act
        data_client = BinanceLiveDataClientFactory.create(
            loop=self.loop,
            name="BINANCE",
            config=BinanceDataClientConfig(  # noqa (S106 Possible hardcoded password)
                account_type=BinanceAccountType.SPOT,
            ),
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        assert isinstance(data_client, BinanceSpotDataClient)

    def test_create_binance_live_futures_data_client(self, binance_http_client):
        # Arrange, Act
        data_client = BinanceLiveDataClientFactory.create(
            loop=self.loop,
            name="BINANCE",
            config=BinanceDataClientConfig(  # noqa (S106 Possible hardcoded password)
                account_type=BinanceAccountType.FUTURES_USDT,
            ),
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        assert isinstance(data_client, BinanceFuturesDataClient)

    def test_create_binance_spot_exec_client(self, binance_http_client):
        # Arrange, Act
        exec_client = BinanceLiveExecClientFactory.create(
            loop=self.loop,
            name="BINANCE",
            config=BinanceExecClientConfig(  # noqa (S106 Possible hardcoded password)
                account_type=BinanceAccountType.SPOT,
            ),
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        assert isinstance(exec_client, BinanceSpotExecutionClient)

    def test_create_binance_futures_exec_client(self, binance_http_client):
        # Arrange, Act
        exec_client = BinanceLiveExecClientFactory.create(
            loop=self.loop,
            name="BINANCE",
            config=BinanceExecClientConfig(  # noqa (S106 Possible hardcoded password)
                account_type=BinanceAccountType.FUTURES_USDT,
            ),
            msgbus=self.msgbus,
            cache=self.cache,
            clock=self.clock,
            logger=self.logger,
        )

        assert isinstance(exec_client, BinanceFuturesExecutionClient)
