from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def process(self, data):
        """
        Process the input data and return the result.
        """
        pass
