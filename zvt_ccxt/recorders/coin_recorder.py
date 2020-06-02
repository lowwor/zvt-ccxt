import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt_ccxt.accounts import CCXTAccount
from zvt_ccxt.schemas import Coin
from zvt_ccxt.settings import COIN_EXCHANGES, COIN_PAIRS


class CoinMetaRecorder(Recorder):
    provider = 'ccxt'
    data_schema = Coin

    def __init__(self, batch_size=10, force_update=False, sleeping_time=10, exchanges=COIN_EXCHANGES) -> None:
        super().__init__(batch_size, force_update, sleeping_time)
        self.exchanges = exchanges

    def run(self):
        for exchange_str in self.exchanges:
            exchange = CCXTAccount.get_ccxt_exchange(exchange_str)
            try:
                markets = exchange.fetch_markets()
                df = pd.DataFrame()

                # markets有些为key=symbol的dict,有些为list
                markets_type = type(markets)
                if markets_type != dict and markets_type != list:
                    self.logger.exception("unknown return markets type {}".format(markets_type))
                    return

                aa = []
                for market in markets:
                    if markets_type == dict:
                        name = market
                        code = market

                    if markets_type == list:
                        code = market['symbol']
                        name = market['symbol']

                    if name not in COIN_PAIRS:
                        continue
                    aa.append(market)

                    security_item = {
                        'id': '{}_{}_{}'.format('coin', exchange_str, code),
                        'entity_id': '{}_{}_{}'.format('coin', exchange_str, code),
                        'exchange': exchange_str,
                        'entity_type': 'coin',
                        'code': code,
                        'name': name
                    }

                    df = df.append(security_item, ignore_index=True)

                # 存储该交易所的数字货币列表
                if not df.empty:
                    df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=True)
                self.logger.info("init_markets for {} success".format(exchange_str))
            except Exception as e:
                self.logger.exception(f"init_markets for {exchange_str} failed", e)


__all__ = ["CoinMetaRecorder"]

if __name__ == '__main__':
    CoinMetaRecorder().run()
