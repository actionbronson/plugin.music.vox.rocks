from abc import ABC


class XbmcAction(ABC):
    def perform(self, context, args):
        pass
