"""
the implementations_stack manages implementation picking
and fallback preferences

based on the contexts pushed/poped from the stack it will choose
context roots and help picking implementations
"""
from contextlib import contextmanager
from collections import namedtuple

LIMIT = 20

ImplementationChoice = namedtuple('ImplementationChoice', 'key, implementation, is_fallback')


class Chooser(namedtuple("Chooser", "elements, previous, frozen")):

    @classmethod
    def make(cls, current, elements, frozen):
        if current is not None and current.frozen:
            raise RuntimeError(
                "further nesting of implementation choice has been disabled"
            )
        if frozen:
            assert len(elements) == 1

        return cls(elements, current, frozen)

    def choose(self, choose_from):
        """given a mapping of implementations
        choose one based on the current settings
        returns a key value pair
        """

        for choice in self.elements:
            if choice in choose_from:
                return ImplementationChoice(choice, choose_from[choice], False)
        raise LookupError(self.elements, choose_from.keys())


class NullChooser(object):
    frozen = False

    def choose(self, *_, **__):
        raise LookupError("No choice possible without valid context")


def chain(element):
    elements = []
    while not isinstance(element, NullChooser):
        elements.append(element)
        element = element.previous
    elements.reverse()
    return elements


class ChooserStack(object):

    def __init__(self, default_elements=None):
        if default_elements is not None:
            self.current = Chooser(
                elements=default_elements, previous=NullChooser(), frozen=False
            )
        else:
            self.current = NullChooser()

    def __repr__(self):
        return "<ICS {chain}>".format(chain=chain(self.current))

    def choose(self, choose_from):
        """given a mapping of implementations
        choose one based on the current settings
        returns a key value pair
        """
        return self.current.choose(choose_from)

    def choose_or_fallback(self, choose_from, fallback):
        try:
            return self.choose(choose_from)
        except LookupError:
            if fallback is None:
                raise
            return fallback

    @contextmanager
    def pushed(self, new, frozen=False):
        self.current = Chooser.make(self.current, new, frozen)
        try:
            if len(chain(self.current)) > LIMIT:
                raise OverflowError("stack depth exceeded")
            yield
        finally:
            self.current = self.current.previous

    @contextmanager
    def pushed_preferred(self, new_preferences):
        assert set(new_preferences).intersection(self.current.elements)
        new = [
            x for x in self.current.elements
            if x in new_preferences
        ] + [
            x for x in self.current.elements
            if x not in new_preferences
        ]

        self.current = Chooser.make(self.current, new, False)
        try:
            if len(chain(self.current)) > LIMIT:
                raise OverflowError("stack depth exceeded")
            yield
        finally:
            self.current = self.current.previous
