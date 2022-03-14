from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class All:
    pass


class Nothing:
    pass


@dataclass
class AllBut:
    exceptions: List[str] = field(default_factory=list)


@dataclass
class Only:
    exceptions: List[str] = field(default_factory=list)


class FilePolicy(ABC):
    All = All
    Nothing = Nothing
    AllBut = AllBut
    Only = Only
