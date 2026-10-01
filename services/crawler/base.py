from abc import ABC, abstractmethod
from typing import Iterable
from models import NormalizedJob


class JobSource(ABC):
    name: str
    acquisition_strategy: str = "html"

    def configure_runtime(self, client) -> None:
        """Inject runtime services such as persistent source-state storage."""
        self.runtime_client = client

    @abstractmethod
    def fetch(self) -> Iterable[NormalizedJob]:
        raise NotImplementedError
