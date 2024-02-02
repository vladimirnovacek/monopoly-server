
import itertools
import random
from typing import Callable, TypedDict

from interfaces import IController


class CardDict(TypedDict):
    text: str
    command: Callable
    action: str


class CardCommands:

    @staticmethod
    def advance_to_field(field_id: int, controller: IController):
        player = controller.gd.on_turn_uuid
        controller.move_to(field_id, player, check_pass_go=True)

    @staticmethod
    def advance_to_go(controller: IController):
        CardCommands.advance_to_field(controller.gd.fields.GO, controller)

    @staticmethod
    def advance_to_field_5(controller: IController):
        CardCommands.advance_to_field(5, controller)

    @staticmethod
    def advance_to_field_11(controller: IController):
        CardCommands.advance_to_field(11, controller)

    @staticmethod
    def advance_to_field_24(controller: IController):
        CardCommands.advance_to_field(24, controller)

    @staticmethod
    def advance_to_field_39(controller: IController):
        CardCommands.advance_to_field(39, controller)

    @staticmethod
    def advance_to_nearest_station(controller: IController):
        player = controller.gd.on_turn_player
        distance_to_nearest_station = (5 - player.field) % 10
        controller.move_by(distance_to_nearest_station, player.player_uuid)
        # paying double rent has to be handled after rolling dice

    @staticmethod
    def advance_to_nearest_utility(controller: IController):
        player = controller.gd.on_turn_player
        ec, ww = 12, 28
        if ec < player.field <= ww:
            move_to = ww
        else:
            move_to = ec
        controller.move_to(move_to, player.player_uuid, check_pass_go=True)
        # paying rent has to be handled after rolling dice


    @staticmethod
    def collect(cash: int, controller: IController):
        controller.collect(cash, controller.gd.on_turn_uuid)

    @staticmethod
    def collect_10(controller: IController):
        CardCommands.collect(10, controller)

    @staticmethod
    def collect_20(controller: IController):
        CardCommands.collect(20, controller)

    @staticmethod
    def collect_25(controller: IController):
        CardCommands.collect(25, controller)

    @staticmethod
    def collect_50(controller: IController):
        CardCommands.collect(50, controller)

    @staticmethod
    def collect_100(controller: IController):
        CardCommands.collect(100, controller)

    @staticmethod
    def collect_150(controller: IController):
        CardCommands.collect(150, controller)

    @staticmethod
    def collect_200(controller: IController):
        CardCommands.collect(200, controller)

    @staticmethod
    def collect_10_from_everyone(controller: IController):
        on_turn = controller.gd.on_turn_player
        for player in controller.gd.players:
            if player is not on_turn:
                controller.pay(10, player.player_uuid, on_turn.player_uuid)

    @staticmethod
    def get_out_of_jail(controller: IController):
        controller.gd.on_turn_player.get_out_of_jail_cards += 1

    @staticmethod
    def go_back_3_spaces(controller: IController):
        controller.move_by(-3, controller.gd.on_turn_uuid, check_pass_go=False)

    @staticmethod
    def go_to_jail(controller: IController):
        controller.move_to(controller.gd.fields.JAIL)

    @staticmethod
    def general_repairs(controller: IController):
        house_price, hotel_price = 25, 100
        houses, hotels = controller.gd.fields.count_houses(controller.on_turn_player.uuid)
        controller.pay(house_price * houses + hotel_price * hotels, controller.on_turn_player.uuid)

    @staticmethod
    def street_repairs(controller: IController):
        house_price, hotel_price = 40, 115
        houses, hotels = controller.gd.fields.count_houses(controller.on_turn_player.uuid)
        controller.pay(house_price * houses + hotel_price * hotels, controller.on_turn_player.uuid)

    @staticmethod
    def pay(cash: int, controller: IController):
        controller.pay(cash, controller.gd.on_turn_uuid)

    @staticmethod
    def pay_15(controller: IController):
        CardCommands.pay(15, controller)

    @staticmethod
    def pay_50(controller: IController):
        CardCommands.pay(50, controller)

    @staticmethod
    def pay_100(controller: IController):
        CardCommands.pay(100, controller)

    @staticmethod
    def pay_50_to_everyone(controller: IController):
        on_turn = controller.gd.on_turn_player
        for player in controller.gd.players:
            if player is not on_turn:
                controller.pay(50, on_turn.player_uuid, player.player_uuid)


class Card:
    def __init__(self, text: str, command: Callable, card_type: str, ends_turn: bool = False, special_rent: str = ""):
        self.text = text
        self.command = command
        self.type = card_type
        self.ends_turn: bool = ends_turn
        self.special_rent: str = special_rent

    def apply(self, controller: IController):
        self.command(controller)

    def is_move(self) -> bool:
        """
        True if the action ordered by this card is moving.
        :return:
        """
        return self.type == "move"



class CardDeck:

    CHANCE = "chance"
    CC = "cc"

    _CHANCE_CARDS: list[CardDict] = [
        {"text": "Advance to Go (Collect £200)",
         "command": CardCommands.advance_to_go, "card_type": "move"},  # 0
        {"text": "Advance to Trafalgar Square. If you pass Go, collect £200",
         "command": CardCommands.advance_to_field_24, "card_type": "move"},  # 1
        {"text": "Advance to Mayfair",
         "command": CardCommands.advance_to_field_39, "card_type": "move"},  # 2
        {"text": "Advance to Pall Mall. If you pass Go, collect £200",
         "command": CardCommands.advance_to_field_11, "card_type": "move"},  # 3
        {"text": "Advance to the nearest Station. If unowned, you may buy it "
                 "from the Bank. If owned, pay owner twice the rental to "
                 "which they are otherwise entitled",
         "command": CardCommands.advance_to_nearest_station, "card_type": "move",
         "special_rent": "double"},  # 4
        {"text": "Advance to the nearest Station. If unowned, you may buy it "
                 "from the Bank. If owned, pay owner twice the rental to "
                 "which they are otherwise entitled",
         "command": CardCommands.advance_to_nearest_station, "card_type": "move",
         "special_rent": "double"},  # 5
        {"text": "Advance token to nearest Utility. If unowned, you may buy it "
                 "from the Bank. If owned, throw dice and pay owner a total "
                 "ten times amount thrown",
         "command": CardCommands.advance_to_nearest_utility, "card_type": "move",
         "special_rent": "10xroll"},  # 6
        {"text": "Bank pays you dividend of £50",
         "command": CardCommands.collect_50, "card_type": "collect"},  # 7
        {"text": "Get Out of Jail Free",
         "command": CardCommands.get_out_of_jail,
         "card_type": "get_out_of_jail"},  # 8
        {"text": "Go Back 3 Spaces",
         "command": CardCommands.go_back_3_spaces, "card_type": "move"},  # 9
        {"text": "Go to Jail. Go directly to Jail, do not pass Go, do not "
                 "collect £200",
         "command": CardCommands.go_to_jail, "card_type": "go_to_jail", "ends_turn": True},  # 10
        {"text": "Make general repairs on all your property. For each house "
                 "pay £25. For each hotel pay £100",
         "command": CardCommands.general_repairs, "card_type": "pay"},  # 11
        {"text": "Speeding fine £15", "command": CardCommands.pay_15},  # 12
        {"text": "Take a trip to Kings Cross Station. If you pass Go, "
                 "collect £200",
         "command": CardCommands.advance_to_field_5, "card_type": "move"},  # 13
        {"text": "You have been elected Chairman of the Board. Pay each "
                 "player £50",
         "command": CardCommands.pay_50_to_everyone, "card_type": "pay_each"},  # 14
        {"text": "Your building loan matures. Collect £150",
         "command": CardCommands.collect_150, "card_type": "collect"}  # 15
    ]
    _CC_CARDS: list[CardDict] = [
        {"text": "Advance to Go (Collect £200)",
         "command": CardCommands.advance_to_go, "card_type": "move"},
        {"text": "Bank error in your favour. Collect £200",
         "command": CardCommands.collect_200, "card_type": "collect"},
        {"text": "Doctor’s fee. Pay £50",
         "command": CardCommands.pay_50, "card_type": "pay"},
        {"text": "From sale of stock you get £50",
         "command": CardCommands.collect_50, "card_type": "collect"},
        {"text": "Get Out of Jail Free",
         "command": CardCommands.get_out_of_jail, "card_type": "get_out_of_jail"},
        {"text": "Go to Jail. Go directly to jail, do not pass Go, do not "
                 "collect £200",
         "command": CardCommands.go_to_jail, "card_type": "go_to_jail", "ends_turn": True},
        {"text": "Holiday fund matures. Receive £100",
         "command": CardCommands.collect_100, "card_type": "collect"},
        {"text": "Income tax refund. Collect £20",
         "command": CardCommands.collect_20, "card_type": "collect"},
        {"text": "It is your birthday. Collect £10 from every player",
         "command": CardCommands.collect_10_from_everyone, "card_type": "collect_from_each"},
        {"text": "Life insurance matures. Collect £100",
         "command": CardCommands.collect_100, "card_type": "pay"},
        {"text": "Pay hospital fees of £100",
         "command": CardCommands.pay_100, "card_type": "pay"},
        {"text": "Pay school fees of £50",
         "command": CardCommands.pay_50, "card_type": "pay"},
        {"text": "Receive £25 consultancy fee",
         "command": CardCommands.collect_25, "card_type": "collect"},
        {"text": "You are assessed for street repairs. £40 per house. "
                 "£115 per hotel",
         "command": CardCommands.street_repairs, "card_type": "pay"},
        {"text": "You have won second prize in a beauty contest. Collect £10",
         "command": CardCommands.collect_10, "card_type": "collect"},
        {"text": "You inherit £100",
         "command": CardCommands.collect_100, "card_type": "collect"}
    ]

    def __init__(self, deck_type: str) -> None:
        self._deck_type = deck_type
        self._deck: list[Card] = []
        deck = self._CHANCE_CARDS if deck_type == self.CHANCE else self._CC_CARDS
        for card in deck:
            self._deck.append(Card(**card))
        random.shuffle(self._deck)
        self._deck_cycler = itertools.cycle(self._deck)
        self.last_card: Card | None = None

    def draw(self) -> Card:
        self.last_card = next(self._deck_cycler)
        return self.last_card

    def apply_card(self, controller: IController):
        self.last_card.apply(controller)


if __name__ == "__main__":
    deck = CardDeck(CardDeck.CC)

    c = deck.draw()
    print(deck.last_card.text)
