from random import randint


class Roll:
    """
    Class represents a roll of dice. Access particlar dice using the index,
    e.g. Roll[0] returns the first dice.
    """

    def __init__(self, count: int, sides: int):
        self.dice: tuple[int, ...] = tuple(randint(1, sides) for _ in range(count))

    def __getitem__(self, item) -> int:
        return self.dice[item]

    def sum(self) -> int:
        """
        Returns the sum of all the dice.
        :return: The sum of all the dice.
        :rtype: int
        """
        return sum(self.dice)

    def get(self) -> tuple[int, ...]:
        """
        Returns the roll as a tuple of individual dice.
        :return: The roll as a tuple of individual dice.
        :rtype: tuple[int, ...]
        """
        return self.dice

    def is_double(self) -> bool:
        """
        Returns True if all the dice are equal.
        :return: True if all the dice are equal.
        :rtype: bool
        """
        return all(i == self.dice for i in self.dice)


class Dice:

    def __init__(self, count: int = 2, sides: int = 6):
        self.last_roll: Roll | None = None
        self.count = count
        self.sides = sides

    def roll(self, register=True) -> Roll:
        """
        Rolls the dice.
        :param register: If False, the roll will not be accessible via last_roll attribute.
        :type register: bool
        :return: Roll object
        :rtype: Roll
        """
        roll = Roll(self.count, self.sides)
        if register:
            self.last_roll = roll
        return roll