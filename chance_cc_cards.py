
import itertools
import random
import typing

from game_controller import GameController


class Card(typing.TypedDict):
    text: str
    command: typing.Callable
    action: str


class CardCommands:

    @staticmethod
    def advance_to_field(field_id: int, controller: GameController):
        player = controller.gd.on_turn_uuid
        controller.move_to(field_id, player, check_pass_go=True)

    @staticmethod
    def advance_to_go(controller: GameController):
        CardCommands.advance_to_field(controller.gd.fields.GO, controller)

    @staticmethod
    def advance_to_field_5(controller: GameController):
        CardCommands.advance_to_field(5, controller)

    @staticmethod
    def advance_to_field_11(controller: GameController):
        CardCommands.advance_to_field(11, controller)

    @staticmethod
    def advance_to_field_24(controller: GameController):
        CardCommands.advance_to_field(24, controller)

    @staticmethod
    def advance_to_field_39(controller: GameController):
        CardCommands.advance_to_field(39, controller)

    # @staticmethod
    # def go_to_nearest_station(controller: GameController):
    #     player = controller.gd.on_turn_player
    #     nearest_station_id = player.field + (5 - player.field) % 10
    #     controller.move_to(nearest_station_id, player.player_uuid)
    #     # TODO pay double rent, check for passing Go

    @staticmethod
    def advance_to_nearest_station(controller: GameController):
        player = controller.gd.on_turn_player
        distance_to_nearest_station = (5 - player.field) % 10
        controller.move_by(distance_to_nearest_station, player.player_uuid)

    @staticmethod
    def advance_to_nearest_utility(controller: GameController):
        player = controller.gd.on_turn_player
        ec, ww = 12, 28
        if ec < player.field <= ww:
            move_to = ww
        else:
            move_to = ec
        controller.move_to(move_to, player.player_uuid, check_pass_go=True)
        # TODO zaplatit 10x hod kostkou


    @staticmethod
    def collect(cash: int, controller: GameController):
        controller.collect(cash, controller.gd.on_turn_uuid)
    @staticmethod
    def collect_10(controller: GameController):
        CardCommands.collect(10, controller)

    @staticmethod
    def collect_20(controller: GameController):
        CardCommands.collect(20, controller)

    @staticmethod
    def collect_25(controller: GameController):
        CardCommands.collect(25, controller)

    @staticmethod
    def collect_50(controller: GameController):
        CardCommands.collect(50, controller)

    @staticmethod
    def collect_100(controller: GameController):
        CardCommands.collect(100, controller)

    @staticmethod
    def collect_150(controller: GameController):
        CardCommands.collect(150, controller)

    @staticmethod
    def collect_200(controller: GameController):
        CardCommands.collect(200, controller)

    @staticmethod
    def collect_10_from_everyone(controller: GameController):
        on_turn = controller.gd.on_turn_player
        for player in controller.gd.players:
            if player is not on_turn:
                controller.pay(10, player.player_uuid, on_turn.player_uuid)

    @staticmethod
    def get_out_of_jail(controller: GameController):
        controller.gd.on_turn_player.get_out_of_jail_cards += 1

    @staticmethod
    def go_back_3_spaces(controller: GameController):
        controller.move_by(-3, controller.gd.on_turn_uuid, check_pass_go=False)

    @staticmethod
    def go_to_jail(controller: GameController):
        controller.move_to(controller.gd.fields.JAIL)

    @staticmethod
    def general_repairs(controller: GameController):
        pass
        # TODO

    @staticmethod
    def street_repairs(controller: GameController):
        pass
        # TODO

    @staticmethod
    def pay(cash: int, controller: GameController):
        controller.pay(cash, controller.gd.on_turn_uuid)

    @staticmethod
    def pay_15(controller: GameController):
        CardCommands.pay(15, controller)

    @staticmethod
    def pay_50(controller: GameController):
        CardCommands.pay(50, controller)

    @staticmethod
    def pay_100(controller: GameController):
        CardCommands.pay(100, controller)

    @staticmethod
    def pay_50_to_everyone(controller: GameController):
        on_turn = controller.gd.on_turn_player
        for player in controller.gd.players:
            if player is not on_turn:
                controller.pay(50, on_turn.player_uuid, player.player_uuid)


class CardDeck:

    CHANCE = "chance"
    CC = "cc"

    _CHANCE_CARDS: list[Card] = [
        {"text": "Advance to Go (Collect £200)",
         "command": CardCommands.advance_to_go, "action": "move"},  # 0
        {"text": "Advance to Trafalgar Square. If you pass Go, collect £200",
         "command": CardCommands.advance_to_field_24, "action": "move"},  # 1
        {"text": "Advance to Mayfair",
         "command": CardCommands.advance_to_field_39, "action": "move"},  # 2
        {"text": "Advance to Pall Mall. If you pass Go, collect £200",
         "command": CardCommands.advance_to_field_11, "action": "move"},  # 3
        {"text": "Advance to the nearest Station. If unowned, you may buy it "
                 "from the Bank. If owned, pay owner twice the rental to "
                 "which they are otherwise entitled",
         "command": CardCommands.advance_to_nearest_station, "action": "move"},  # 4
        {"text": "Advance to the nearest Station. If unowned, you may buy it "
                 "from the Bank. If owned, pay owner twice the rental to "
                 "which they are otherwise entitled",
         "command": CardCommands.advance_to_nearest_station, "action": "move"},  # 5
        {"text": "Advance token to nearest Utility. If unowned, you may buy it "
                 "from the Bank. If owned, throw dice and pay owner a total "
                 "ten times amount thrown",
         "command": CardCommands.advance_to_nearest_utility, "action": "move"},  # 6
        {"text": "Bank pays you dividend of £50",
         "command": CardCommands.collect_50, "action": "payment"},  # 7
        {"text": "Get Out of Jail Free",
         "command": CardCommands.get_out_of_jail,
         "action": "get_out_og_jail"},  # 8
        {"text": "Go Back 3 Spaces",
         "command": CardCommands.go_back_3_spaces, "action": "move"},  # 9
        {"text": "Go to Jail. Go directly to Jail, do not pass Go, do not "
                 "collect £200",
         "command": CardCommands.go_to_jail, "action": "move"},  # 10
        {"text": "Make general repairs on all your property. For each house "
                 "pay £25. For each hotel pay £100",
         "command": CardCommands.general_repairs, "action": "payment"},  # 11
        {"text": "Speeding fine £15", "command": CardCommands.pay_15},  # 12
        {"text": "Take a trip to Kings Cross Station. If you pass Go, "
                 "collect £200",
         "command": CardCommands.advance_to_field_5, "action": "move"},  # 13
        {"text": "You have been elected Chairman of the Board. Pay each "
                 "player £50",
         "command": CardCommands.pay_50_to_everyone, "action": "payment"},  # 14
        {"text": "Your building loan matures. Collect £150",
         "command": CardCommands.collect_150, "action": "payment"}  # 15
    ]
    _CC_CARDS: list[Card] = [
        {"text": "Advance to Go (Collect £200)",
         "command": CardCommands.advance_to_go, "action": "move"},
        {"text": "Bank error in your favour. Collect £200",
         "command": CardCommands.collect_200, "action": "payment"},
        {"text": "Doctor’s fee. Pay £50",
         "command": CardCommands.pay_50, "action": "payment"},
        {"text": "From sale of stock you get £50",
         "command": CardCommands.collect_50, "action": "payment"},
        {"text": "Get Out of Jail Free",
         "command": CardCommands.get_out_of_jail, "action": "get_out_of_jail"},
        {"text": "Go to Jail. Go directly to jail, do not pass Go, do not "
                 "collect £200",
         "command": CardCommands.go_to_jail, "action": "move"},
        {"text": "Holiday fund matures. Receive £100",
         "command": CardCommands.collect_100, "action": "payment"},
        {"text": "Income tax refund. Collect £20",
         "command": CardCommands.collect_20, "action": "payment"},
        {"text": "It is your birthday. Collect £10 from every player",
         "command": CardCommands.collect_10_from_everyone, "action": "payment"},
        {"text": "Life insurance matures. Collect £100",
         "command": CardCommands.collect_100, "action": "payment"},
        {"text": "Pay hospital fees of £100",
         "command": CardCommands.pay_100, "action": "payment"},
        {"text": "Pay school fees of £50",
         "command": CardCommands.pay_50, "action": "payment"},
        {"text": "Receive £25 consultancy fee",
         "command": CardCommands.collect_25, "action": "payment"},
        {"text": "You are assessed for street repairs. £40 per house. "
                 "£115 per hotel",
         "command": CardCommands.street_repairs, "action": "payment"},
        {"text": "You have won second prize in a beauty contest. Collect £10",
         "command": CardCommands.collect_10},
        {"text": "You inherit £100",
         "command": CardCommands.collect_100, "action": "payment"}
    ]

    def __init__(self, deck_type: str) -> None:
        self._deck_type = deck_type
        self._deck: list[Card]
        match deck_type:
            case self.CHANCE:
                self._deck = self._CHANCE_CARDS.copy()
            case self.CC:
                self._deck = self._CC_CARDS.copy()
            case _:
                raise ValueError("Unknown deck type.")
        random.shuffle(self._deck)
        self._deck_cycler = itertools.cycle(self._deck)
        self._last_card: dict | None = None

    def is_move(self) -> bool:
        """
        True if the action ordered by a last card is moving.
        :return:
        """
        return self._last_card["action"] == "move"

    def draw(self) -> dict:
        self._last_card = next(self._deck_cycler)
        return self._last_card

    def apply_card(self, controller: GameController):
        command = self._last_card["command"]
        command(controller)

    def get_action(self):
        return self._last_card["action"]

    def get_description(self):
        return self._last_card["text"]


if __name__ == "__main__":
    deck = CardDeck(CardDeck.CC)

    c = deck.draw()
    print(deck.get_description())
