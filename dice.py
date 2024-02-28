# -*- tests-case-name: tests.test_dice -*-

from random import randint

from interfaces import IDice, IRoll


class Roll(IRoll):


    def __init__(self, count: int, sides: int):
        self._roll: tuple[int, ...] = tuple(randint(1, sides) for _ in range(count))

    def __getitem__(self, item) -> int:
        return self._roll[item]

    def sum(self) -> int:
        return sum(self._roll)

    def get(self) -> tuple[int, ...]:
        return self._roll

    def is_double(self) -> bool:
        if len(self._roll) < 2:
            return False
        return all(i == self._roll[0] for i in self._roll[1:])


class Dice(IDice):

    def __init__(self, count: int = 2, sides: int = 6):
        self.last_roll: Roll | None = None
        """ The last roll. None if no roll has been made yet. """
        self.count: int = count
        """ The number of dice. """
        self.sides: int = sides
        """ The number of sides of the dice. """
        self.doubles: int = 0
        """ The count of doubles in the row. """

    @property
    def triple_double(self) -> bool:
        return self.doubles >= 3

    def reset(self) -> None:
        self.doubles = 0
        self.last_roll = None

    def roll(self, register=True) -> Roll:
        roll = Roll(self.count, self.sides)
        self.last_roll = roll
        if register:
            if roll.is_double():
                self.doubles += 1
            else:
                self.doubles = 0
        return roll
