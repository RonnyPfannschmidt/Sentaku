import contextlib
import attr
import dectate
from collections import defaultdict
from .chooser import ChooserStack, ImplementationChoice

METHOD_DATA_KEY = "sentaku_method_data"


@attr.s
class ImplementationRegistrationAction(dectate.Action):
    config = {"methods": lambda: defaultdict(dict)}
    method = attr.ib()
    implementation = attr.ib()

    def identifier(self, methods):
        return self.method, self.implementation

    def perform(self, obj, methods):
        methods[self.method][self.implementation] = obj


@attr.s
class FallbackRegistrationAction(dectate.Action):
    config = {
        'fallbacks': dict
    }

    method = attr.ib()
    implementation = attr.ib()

    def identifier(self, fallbacks):
        return self.method

    def perform(self, obj, fallbacks):
        fallbacks[self.method] = ImplementationChoice(
            self.implementation, obj, is_fallback=True)


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
        default=attr.Factory(ChooserStack), converter=ChooserStack
    )
    strict_calls = attr.ib(default=False)

    external_for = dectate.directive(ImplementationRegistrationAction)
    fallback_for = dectate.directive(FallbackRegistrationAction)

    @classmethod
    def with_default_choices(cls, implementations, default_choices, **kw):
        return cls(
            implementations=implementations,
            implementation_chooser=default_choices,
            **kw
        )

    @property
    def impl(self):
        """the currently active implementation"""
        return self.implementation_chooser.choose(self.implementations).implementation

    def _get_implementation_for(self, key):
        self.commit()
        implementation_set = self.config.methods[key]

        return self.implementation_chooser.choose(implementation_set)

    def call_implementation_for(self, key, instance, args=(), kwargs=None):
        self.commit()
        kwargs = kwargs or {}
        implementation_set = self.config.methods[key]
        fallback = self.config.fallbacks.get(key)
        choice = self.implementation_chooser.choose_or_fallback(
            implementation_set, fallback)
        bound_method = choice.implementation.__get__(instance, type(instance))
        with self._use_for_call(choice.key, choice.is_fallback):
            return bound_method(*args, **kwargs)

    @classmethod
    def from_instances(cls, instances, **kw):
        """utility to create the context

        by passing a ordered list of instances
        and turning them into implementations and the default choices
        """
        return cls.with_default_choices(
            implementations={type(x): x for x in instances},
            default_choices=[type(x) for x in instances],
            **kw
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
            implementation_types, frozen=_get_frozen(**kw)
        ):
            yield self.impl

    @contextlib.contextmanager
    def use_strict(self, impl):
        with self.use(impl, frozen=True) as imp:
            yield imp

    @contextlib.contextmanager
    def use_preferred(self, impl):
        with self.implementation_chooser.pushed_preferred([impl]) as imp:
            yield imp

    @contextlib.contextmanager
    def _use_for_call(self, impl, is_fallback):
        if self.strict_calls or is_fallback:
            ctx = self.use_strict
        else:
            ctx = self.use_preferred
        with ctx(impl) as imp:
            yield imp


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
        return self.instance.context.call_implementation_for(
            self.selector, self.instance, k, kw)


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
    def __repr__(self):
        return "<ContextualMethod>"

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
        self.setter = self, "set"
        self.getter = self, "get"

    def external_setter_implemented_for(self, implementation):
        return ImplementationContext.external_for(self.setter, implementation)

    def external_getter_implemented_for(self, implementation):
        return ImplementationContext.external_for(self.getter, implementation)

    def __set__(self, instance, value):
        return instance.context.call_implementation_for(
            self.setter, instance, (value, ))

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.context.call_implementation_for(self.getter, instance)
