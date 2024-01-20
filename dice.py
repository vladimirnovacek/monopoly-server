# -*- tests-case-name: tests.test_dice -*-

from random import randint


class Roll:
    """
    Class represents a roll of dice. Access particlar dice using the index,
    e.g. Roll[0] returns the first dice.
    """

    def __init__(self, count: int, sides: int):
        self._roll: tuple[int, ...] = tuple(randint(1, sides) for _ in range(count))

    def __getitem__(self, item) -> int:
        return self._roll[item]

    def sum(self) -> int:
        """
        Returns the sum of all the dice.
        :return: The sum of all the dice.
        :rtype: int
        """
        return sum(self._roll)

    def get(self) -> tuple[int, ...]:
        """
        Returns the roll as a tuple of individual dice.
        :return: The roll as a tuple of individual dice.
        :rtype: tuple[int, ...]
        """
        return self._roll

    def is_double(self) -> bool:
        """
        Returns True if all the dice are equal.
        :return: True if all the dice are equal.
        :rtype: bool
        """
        if len(self._roll) < 2:
            return False
        return all(i == self._roll[0] for i in self._roll[1:])


class Dice:

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
        """
        Returns True if three doubles in a row.
        :return: True if three doubles in a row.
        :rtype: bool
        """
        return self.doubles >= 3

    def reset(self) -> None:
        """
        Resets the dice.
        :return:
        :rtype:
        """
        self.doubles = 0
        self.last_roll = None

    def roll(self, register=True) -> Roll:
        """
        Rolls the dice.
        :param register: If True, the roll will be stored in the last_roll attribute and counts toward doubles.
        :type register: bool
        :return: Roll object
        :rtype: Roll
        """
        roll = Roll(self.count, self.sides)
        if register:
            self.last_roll = roll
            if roll.is_double():
                self.doubles += 1
            else:
                self.doubles = 0
        return roll
