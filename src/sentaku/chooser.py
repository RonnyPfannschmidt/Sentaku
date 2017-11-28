"""
the implementations_stack manages implementation picking
and fallback preferences

based on the contexts pushed/poped from the stack it will choose
context roots and help picking implementations
"""
from collections import namedtuple
from contextlib import contextmanager

import attr


LIMIT = 20

ImplementationChoice = namedtuple('ImplementationChoice', 'key, value')


@attr.s(frozen=True)
class NullChooser(object):
    frozen = False

    def choose(self, *_, **__):
        raise LookupError('No choice possible without valid context')


@attr.s(frozen=True)
class Chooser(object):
    elements = attr.ib()
    previous = attr.ib(default=NullChooser())
    frozen = attr.ib(default=False)

    @classmethod
    def make(cls, current, elements, frozen):
        if current is not None and current.frozen:
            raise RuntimeError(
                'further nesting of implementation choice has been disabled')
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
                return ImplementationChoice(choice, choose_from[choice])
        raise LookupError(self.elements, choose_from.keys())


def chain(element):
    elements = []
    while not isinstance(element, NullChooser):
        elements.append(element)
        element = element.previous
    elements.reverse()
    return elements


@attr.s
class ChooserStack(object):
    current = attr.ib(default=NullChooser())

    @classmethod
    def from_elements(cls, default_elements):
        if default_elements is not None:
            return cls(Chooser(elements=default_elements))
        else:
            return cls()

    def __repr__(self):
        return '<ICS {chain}>'.format(chain=chain(self.current))

    def choose(self, choose_from):
        """given a mapping of implementations
        choose one based on the current settings
        returns a key value pair
        """
        return self.current.choose(choose_from)

    @contextmanager
    def pushed(self, new, frozen=False):
        self.current = Chooser.make(self.current, new, frozen)
        try:
            if len(chain(self.current)) > LIMIT:
                raise OverflowError("stack depth exceeded")
            yield
        finally:
            self.current = self.current.previous
