from abc import ABC, abstractmethod
from typing import Iterable
from models import NormalizedJob


class JobSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> Iterable[NormalizedJob]:
        raise NotImplementedError
