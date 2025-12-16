from abc import ABC, abstractmethod

class SearchProvider(ABC):
    @abstractmethod
    def search(self):
        pass