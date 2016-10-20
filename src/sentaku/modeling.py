import warnings



class Element(object):
    """Base class for all application elements

    :param parent:
        controlling object of the element which is either a context
        or a surrounding element
    :type parent: :py:class:`Element` or :py:class:`ImplementationContext`
    """
    def __init__(self, parent):
        self.parent = parent

    @property
    def context(self):
        """the context this element belongs to"""
        return self.parent.context

    @property
    def root(self):
        warnings.warn(
            "Element.root got renamed to .context",
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.context

    @property
    def impl(self):
        """shortcut to get the currently active application implementation"""
        return self.context.impl


class Collection(Element):
    """base class for collections in the application

    :todo: generic helpers for querying
    """
