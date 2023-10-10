from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from abc import ABC, abstractmethod
from itertools import count
from random import Random
from typing import Iterator


@dataclass
class AssetPrice:
    """ Котировальный список активов """
    LKOH: Decimal = Decimal(5896)  # цена по умолчанию
    SBER: Decimal = Decimal(250)


class AssetPriceHistory(ABC):
    """
    История цен активов.

    Можно переопределять в дочерних классах, чтобы симулировать различные ситуации.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[tuple[date, AssetPrice]]:
        """
        Возвращает историю цен активов - кортежи вида (дата, цены активов).
        """
        ...


@dataclass
class ChaosAssetPriceHistory(AssetPriceHistory):
    """
    История цен активов, в которой цены меняются случайным образом.

    Только для самых отчаянных трейдеров.
    """

    price_multiplier: tuple[float, float] = (0.5, 1.5)  # множитель цены актива; по умолчанию актив может просесть на 50% или взлететь на 50% за один день, хе-хе
    seed: int = 42

    def __post_init__(self):
        self.random = Random()
        self.random.seed(self.seed)

    def __iter__(self) -> Iterator[tuple[date, AssetPrice]]:
        today = date.today()
        base_asset_price = AssetPrice()
        for day in count():
            date_ = today + timedelta(days=day)
            if day == 0:
                asset_price = base_asset_price
            else:
                asset_price = AssetPrice(**{
                    field: getattr(base_asset_price, field) * multiplier
                    for field in AssetPrice.__dataclass_fields__.keys()
                    if (multiplier := Decimal(self.random.uniform(*self.price_multiplier)))
                })

            yield date_, asset_price


@dataclass
class ChillAssetPriceHistory(AssetPriceHistory):
    """
    История цен активов, в которой цены не меняются.

    Когда устали от трейдинга и просто хотите не думать.
    """

    def __iter__(self) -> Iterator[tuple[date, AssetPrice]]:
        today = date.today()
        asset_price = AssetPrice()
        for day in count():
            date_ = today + timedelta(days=day)
            yield date_, asset_price


@dataclass
class RealAssetPriceHistory(AssetPriceHistory):
    """
    Настоящая история цен активов, взятая из исторических данных.

    Без шуток.

    В дальнейшем можно брать по API откуда-нибудь.
    """

    def __iter__(self) -> Iterator[tuple[date, AssetPrice]]:
        yield from (
            (date(2023, 9, 10), AssetPrice(LKOH=Decimal(6669), SBER=Decimal(255))),
            (date(2023, 9, 11), AssetPrice(LKOH=Decimal(6456), SBER=Decimal(256))),
            (date(2023, 9, 12), AssetPrice(LKOH=Decimal(6729), SBER=Decimal(262))),
            (date(2023, 9, 13), AssetPrice(LKOH=Decimal(6610), SBER=Decimal(258))),
            (date(2023, 9, 14), AssetPrice(LKOH=Decimal(6519), SBER=Decimal(260))),
            (date(2023, 9, 15), AssetPrice(LKOH=Decimal(6553), SBER=Decimal(260))),
            (date(2023, 9, 16), AssetPrice(LKOH=Decimal(6527), SBER=Decimal(260))),
            (date(2023, 9, 17), AssetPrice(LKOH=Decimal(6566), SBER=Decimal(263))),
        )


if __name__ == '__main__':
    # Пример использования
    from itertools import islice

    for class_ in {ChaosAssetPriceHistory, ChillAssetPriceHistory, RealAssetPriceHistory}:
        print('-' * 10, class_.__name__, '-' * 10)
        history = class_()
        for date_, asset_price in islice(history, 10):  # islice, потому что мы не хотим до бесконечности
            print(date_, asset_price)
