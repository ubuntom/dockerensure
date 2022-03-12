from abc import ABC
from dataclasses import dataclass, field
from typing import List
from enum import Enum


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
