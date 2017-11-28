import contextlib
from collections import defaultdict

import attr

import dectate

from .chooser import ChooserStack

METHOD_DATA_KEY = 'sentaku_method_data'


@attr.s
class ImplementationRegistrationAction(dectate.Action):
    config = {
        'methods': lambda: defaultdict(dict)
    }
    method = attr.ib()
    implementation = attr.ib()

    def identifier(self, methods):
        return self.method, self.implementation

    def perform(self, obj, methods):
        methods[self.method][self.implementation] = obj


@attr.s(hash=False)
class ImplementationContext(dectate.App):
    """ maintains a mapping
    of :ref:`implementation-identification` to implementations,
    as well as the list of currently availiable Implementations
    in the order of precedence.

    :type implementations: `collections.Mapping`
    :param implementations:
        the implementations availiable in the context

        a mapping of :ref:`implementation-identification` to implementation
    :param default_choices:
        the implementations that should be used by default
        in order of percedence
    :type default_choices: optional list
    """

    implementations = attr.ib()
    implementation_chooser = attr.ib(
        default=attr.Factory(ChooserStack),
        convert=ChooserStack.from_elements)
    strict_calls = attr.ib(default=False)

    external_for = dectate.directive(ImplementationRegistrationAction)

    @classmethod
    def with_default_choices(cls, implementations, default_choices):
        return cls(
            implementations=implementations,
            implementation_chooser=default_choices,
        )

    @property
    def impl(self):
        """the currently active implementation"""
        return self.implementation_chooser.choose(
            self.implementations).value

    def _get_implementation_for(self, key):
        self.commit()
        implementation_set = self.config.methods[key]
        return self.implementation_chooser.choose(implementation_set)

    @classmethod
    def from_instances(cls, instances):
        """utility to create the context

        by passing a ordered list of instances
        and turning them into implementations and the default choices
        """
        return cls.with_default_choices(
            implementations={type(x): x for x in instances},
            default_choices=[type(x) for x in instances],
        )

    @property
    def context(self):
        """alias for consistence with elements"""
        return self

    root = context

    @contextlib.contextmanager
    def use(self, *implementation_types, **kw):
        """contextmanager for controlling
        the currently active/usable implementations and
        their order of percedence

        :param `implementation-identification` implementation_types:
            the implementations availiable within the context
        :keyword bool frozen: if True prevent further nesting
        """
        def _get_frozen(frozen=False):
            return frozen

        with self.implementation_chooser.pushed(
                implementation_types, frozen=_get_frozen(**kw)):
            yield self.impl


@attr.s
class _ImplementationBindingMethod(object):
    """bound method equivalent for :class:`ImplementationCooser`

    on call it:

    * looks up the implementation
    * freezes the context
    * calls the actual implementation
    """
    instance = attr.ib()
    selector = attr.ib()

    def __call__(self, *k, **kw):
        ctx = self.instance.context
        choice, implementation = ctx._get_implementation_for(self.selector)
        bound_method = implementation.__get__(
            self.instance, type(self.instance))
        with ctx.use(choice, frozen=ctx.strict_calls):
            return bound_method(*k, **kw)


@attr.s(cmp=False)
class ContextualMethod(object):
    """
    descriptor for implementing context sensitive methods
    and registration of their implementations


    .. code:: python

        class Example(Element):
            action = ContextualMethod()
            @action.implemented_for("db")
            def action(self):
                pass

           @action.implemented_for("test")
           def action(self):
               pass
    """
    # todo - turn into attrs class once attribute ancoring is implemented

    def external_implementation_for(self, implementation):
        return ImplementationContext.external_for(self, implementation)

    def __get__(self, instance, *_ignored):
        if instance is None:
            return self
        return _ImplementationBindingMethod(instance=instance, selector=self)


class ContextualProperty(object):
    # todo - turn into attrs class once attribute ancoring is implemented
    def __init__(self):
        # setter and getter currently are lookup keys
        self.setter = self, 'set'
        self.getter = self, 'get'

    def external_setter_implemented_for(self, implementation):
        return ImplementationContext.external_for(self.setter, implementation)

    def external_getter_implemented_for(self, implementation):
        return ImplementationContext.external_for(self.getter, implementation)

    def __set__(self, instance, value):

        ctx = instance.context
        choice, implementation = ctx._get_implementation_for(self.setter)

        bound_method = implementation.__get__(instance, type(instance))
        with ctx.use(choice, frozen=True):
            return bound_method(value)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        ctx = instance.context
        choice, implementation = ctx._get_implementation_for(self.getter)

        bound_method = implementation.__get__(instance, type(instance))
        with ctx.use(choice, frozen=True):
            return bound_method()
