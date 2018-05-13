from sentaku.context import ImplementationContext, ContextualProperty, ContextualMethod
from sentaku import Element

import attr
import pytest


def test_from_instances():
    ctx = ImplementationContext.from_instances([1, "a"])
    assert ctx.implementation_chooser.current.elements == [int, str]
    assert ctx.implementations == {int: 1, str: "a"}


class LocalContext(ImplementationContext):
    pass


class LocalElement(Element):
    method = ContextualMethod()
    prop = ContextualProperty()


@LocalContext.external_for(LocalElement.method, int)
@LocalContext.external_for(LocalElement.method, str)
@LocalContext.external_for(LocalElement.prop.setter, int)
@LocalContext.external_for(LocalElement.prop.setter, str)
@LocalContext.external_for(LocalElement.prop.getter, int)
@LocalContext.external_for(LocalElement.prop.getter, str)
def method_standin(self, value=None):
    assert (
        self.context.implementation_chooser.current.frozen == self.context.strict_calls
    )


@pytest.fixture(
    params=[
        pytest.param(True, id="nest=strict"), pytest.param(False, id="nest=lenient")
    ]
)
def ctx(request):
    return LocalContext.from_instances([1, 'a', object], strict_calls=request.param)


@pytest.fixture
def elem(ctx):
    return LocalElement(parent=ctx)


@pytest.fixture(params=(int, str))
def impl(request):
    return request.param


def test_property(ctx, elem, impl):
    with ctx.use(impl):
        elem.prop


def test_set_property(ctx, elem, impl):
    with ctx.use(impl):
        elem.prop = 1


def test_method(ctx, elem, impl):
    with ctx.use(impl):
        elem.method()


@attr.s
class FallbackElement(Element):
    fallback_triggered = attr.ib(default=False)

    method = ContextualMethod()


@LocalContext.fallback_for(FallbackElement.method, type)
def fallback_type(self):
    self.fallback_triggered = True
    return self.impl


def test_fallback(ctx):
    elem = FallbackElement(ctx)
    res = elem.method()

    assert res is object
