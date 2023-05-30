import math
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import cached_property


@dataclass
class Fixed:
    mantissa: int
    exponent: int

    @classmethod
    def from_float(cls, val: float, places: int):
        base_exponent = math.floor(math.log10(val))
        exponent = int(base_exponent - places)
        mantissa = int(round(val / 10**exponent))
        return cls(mantissa, exponent)

    def as_float(self):
        return float(self.mantissa) * 10**self.exponent


class ValueColor(IntEnum):
    black = 0
    brown = 1
    red = 2
    orange = 3
    yellow = 4
    green = 5
    blue = 6
    violet = 7
    gray = 8
    grey = 8
    white = 9


class ExponentColor(IntEnum):
    black = 0
    brown = 1
    red = 2
    orange = 3
    yellow = 4
    green = 5
    blue = 6
    violet = 7
    gold = -1
    silver = -2
    pink = -3

    @cached_property
    def multiplier(self):
        return 10.0**self.value


class TolerancePercentColor(float, Enum):
    brown = 1.0
    red = 2.0
    green = 0.5
    blue = 0.25
    violet = 0.1
    gray = 0.05
    grey = 0.05
    gold = 5.0
    silver = 10.0
    none = 20.0


def si_prefixer(value: float) -> tuple[float, str]:
    prefixes = {
        3: "k",
        6: "M",
    }
    for exp, prefix in sorted(prefixes.items(), reverse=True):
        if math.floor(value / 10**exp):
            break
    else:
        raise ValueError(f"Couldn't find prefix for {value}.")
    return value / 10**exp, prefix


@dataclass
class ResistorValue:
    fixed: Fixed

    @classmethod
    def from_float(cls, val: float):
        return cls(Fixed.from_float(val, 2))

    @classmethod
    def from_three_bands(cls, first: str, second: str, exponent: str):
        value = ValueColor[first] * 10 + ValueColor[second]
        exp_val = ExponentColor[exponent]
        return cls(Fixed(value, exp_val))

    @classmethod
    def from_four_bands(cls, first: str, second: str, third: str, exponent: str):
        value = ValueColor[first] * 100 + ValueColor[second] * 10 + ValueColor[third]
        exp_val = ExponentColor[exponent]
        return cls(Fixed(value, exp_val))

    def as_three_bands(self) -> tuple[str, str, str]:
        dec = Fixed.from_float(self.fixed.as_float(), 1)
        first = ValueColor(dec.mantissa // 10)
        second = ValueColor(dec.mantissa % 10)
        exponent = ExponentColor(dec.exponent)
        return first.name, second.name, exponent.name

    def as_four_bands(self) -> tuple[str, str, str, str]:
        fixed = Fixed.from_float(self.fixed.as_float(), 2)
        first = ValueColor(fixed.mantissa // 100)
        second = ValueColor((fixed.mantissa - (first * 100)) // 10)
        third = ValueColor(fixed.mantissa % 10)
        exponent = ExponentColor(fixed.exponent)
        return first.name, second.name, third.name, exponent.name

    @property
    def value(self) -> float:
        return self.fixed.as_float()

    def __str__(self):
        try:
            return "{:g} {}Ω".format(*si_prefixer(self.value)).strip()
        except ValueError:
            return f"{self.value:g}Ω"
