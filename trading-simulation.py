"""
Напишите программу для симуляции торговли на финансовых рынках, включая методы для выполнения транзакций покупки и продажи активов и получения текущей стоимости портфеля.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from textwrap import dedent
from time import sleep

from history import AssetPriceHistory, RealAssetPriceHistory


class NotEnoughCash(Exception):
    pass


class WrongAssetName(ValueError):
    pass


class NotEnoughAsset(Exception):
    pass


class StopGameException(Exception):
    pass


def input_int(text: str) -> int:
    while True:
        try:
            return int(input(text))
        except ValueError:
            print("Неправильный ввод, попробуйте ещё раз. Нужно число!")


@dataclass
class PortfolioSimulator:
    history: AssetPriceHistory = field(default_factory=RealAssetPriceHistory)  # dependency injection такое, можно подставлять разные истории и тренироваться на разных данных
    cash: Decimal = Decimal(100_000)  # начальный капитал
    assets: defaultdict = field(default_factory=lambda: defaultdict(int))  # сколько активов у нас есть (в начале мы ничего не имеем)

    def __post_init__(self):
        if self.cash < 0:
            raise NotEnoughCash("Начальный капитал не может быть отрицательным")

        self.days = iter(self.history)
        self.next_day()  # получаем первую дату и цены активов
        self.initial_value = self.value
        self.logo = (Path(__file__).parent / 'logo.txt').read_text()

    def next_day(self):
        """ Закончить день и получить цены нового дня """
        self.current_date, self.current_prices = next(self.days)

    def buy(self, asset: str, amount: int):
        """ Купить актив """

        try:
            price = getattr(self.current_prices, asset)
        except AttributeError as exc:
            raise WrongAssetName(f"Нет такого актива: {asset}") from exc
        cost = price * amount

        if self.cash < cost:
            raise NotEnoughCash(f"Недостаточно денег для покупки актива: требуется {cost}, а есть {self.cash}")

        self.cash -= cost
        self.assets[asset] += amount

    def sell(self, asset: str, amount: int):
        """ Продать актив """

        if asset not in self.assets:
            raise WrongAssetName(f"Нет такого актива: {asset}")

        if (current_quantity := self.assets[asset]) < amount:
            raise NotEnoughAsset(f"Недостаточно актива для продажи: требуется {amount}, а есть {current_quantity}")

        try:
            self.cash += getattr(self.current_prices, asset) * amount
        except AttributeError as exc:
            raise WrongAssetName(f"Нет такого актива: {asset}") from exc
        self.assets[asset] -= amount

    @property
    def asset_values(self) -> list[tuple[str, int, Decimal]]:
        """ Стоимость активов """
        return [
            (asset, quantity, getattr(self.current_prices, asset) * quantity)
            for asset in self.current_prices.__dataclass_fields__.keys()
            if (quantity := self.assets[asset]) != 0  # не показываем то, чего не имеем
        ]

    @property
    def value(self) -> Decimal:
        """ Стоимость портфеля """
        return self.cash + sum(price for _, _, price in self.asset_values)

    @property
    def profit(self) -> Decimal:
        """ Прибыль """
        return self.value - self.initial_value

    def run(self):
        """ Интерактивный режим """
        self.print_greeting()

        while True:
            self.print_summary()
            try:
                self.user_action()
            except StopGameException:
                break

        self.print_result()

    def print_greeting(self):
        print(self.logo)
        print('Добро пожаловать в симулятор торговли активами!')
        print('Постарайтесь не разориться в первый день :>')

    def print_summary(self):
        print('-' * 40)
        print(f"Дата: {self.current_date}")

        print("Ваши активы:")
        asset = None
        for asset, quantity, total in self.asset_values:
            print('\t'.join([asset, f'{quantity}шт', f'{total:,.2f}₽']))
        if not asset:
            print("\t(пусто)")

        print(f"Ваши деньги: {self.cash:,.2f}₽")
        print(f"Стоимость портфеля: {self.value:,.2f}₽")
        print(f"Прибыль: {self.profit:,.2f}₽")

        print('')
        print('Цены активов на сегодня:')
        for asset in self.current_prices.__dataclass_fields__.keys():
            price = getattr(self.current_prices, asset)
            print('\t'.join([asset, f'{price:,.2f}₽']))

    def user_action(self) -> bool:
        """ Выбор действия пользователя """

        match input(dedent("""
            Что вы хотите сделать?
            1. Купить актив
            2. Продать актив
            3. Закончить день
            4. Зафиксировать значения и завершить программу
        """)):
            case "1":
                asset = input("Какой актив вы хотите купить? ")
                amount = input_int("Сколько? ")
                try:
                    self.buy(asset, amount)
                except (WrongAssetName, NotEnoughCash) as exc:
                    print(exc)
                else:
                    print(f"Вы купили {amount} {asset}")
                sleep(1)

            case "2":
                asset = input("Какой актив вы хотите продать? ")
                amount = input_int("Сколько? ")
                try:
                    self.sell(asset, amount)
                except (WrongAssetName, NotEnoughAsset) as exc:
                    print(exc)
                else:
                    print(f"Вы продали {amount} {asset}")
                sleep(1)

            case "3":
                try:
                    self.next_day()
                except StopIteration as exc:
                    raise StopGameException() from exc

            case "4":
                raise StopGameException()

            case _:
                print("Неправильный выбор, попробуйте ещё раз.")

    def print_result(self):
        if (profit := self.profit) > 0:
            print("Stonks! Вы закончили торговлю с прибылью! Отправляю данные о вас в налоговую! }:)")
        elif profit == 0:
            print("Ну вы хоть не разорились, это уже хорошо")
        else:
            print("Not stonks! Вы закончили торговлю в минус! Штош, бывает :[")


if __name__ == '__main__':
    from argparse import ArgumentParser
    import inspect
    import history

    history_classes = {
        name.removesuffix('AssetPriceHistory').lower(): class_
        for name, class_ in inspect.getmembers(history, inspect.isclass)
        if issubclass(class_, AssetPriceHistory) and class_ != AssetPriceHistory
    }

    parser = ArgumentParser()
    parser.add_argument(
        '--history',
        choices=history_classes.keys(),
        default=next(iter(history_classes.keys())),
        help='Какую историю использовать',
    )
    parser.add_argument(
        '--cash',
        type=Decimal,
        default=Decimal(100_000),
        help='Сколько денег в начале',
    )
    args = parser.parse_args()

    simulator = PortfolioSimulator(
        history=history_classes[args.history](),
        cash=args.cash,
    )
    simulator.run()
