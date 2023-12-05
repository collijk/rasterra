import operator
from typing import Any, Callable

from rasterra._ops import roperator


class OpsMixin:
    # -------------------------------------------------------------
    # Comparisons

    def _cmp_method(self, other: Any, op: Callable) -> Any:
        return NotImplemented

    def __eq__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.eq)

    def __ne__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.ne)

    def __lt__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.lt)

    def __le__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.le)

    def __gt__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.gt)

    def __ge__(self, other: Any) -> Any:
        return self._cmp_method(other, operator.ge)

    # -------------------------------------------------------------
    # Logical Methods

    def _logical_method(self, other: Any, op: Callable) -> Any:
        return NotImplemented

    def __and__(self, other: Any) -> Any:
        return self._logical_method(other, operator.and_)

    def __rand__(self, other: Any) -> Any:
        return self._logical_method(other, roperator.rand_)

    def __or__(self, other: Any) -> Any:
        return self._logical_method(other, operator.or_)

    def __ror__(self, other: Any) -> Any:
        return self._logical_method(other, roperator.ror_)

    def __xor__(self, other: Any) -> Any:
        return self._logical_method(other, operator.xor)

    def __rxor__(self, other: Any) -> Any:
        return self._logical_method(other, roperator.rxor)

    # -------------------------------------------------------------
    # Arithmetic Methods

    def _arith_method(self, other: Any, op: Callable) -> Any:
        return NotImplemented

    def __add__(self, other: Any) -> Any:
        return self._arith_method(other, operator.add)

    def __radd__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.radd)

    def __sub__(self, other: Any) -> Any:
        return self._arith_method(other, operator.sub)

    def __rsub__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rsub)

    def __mul__(self, other: Any) -> Any:
        return self._arith_method(other, operator.mul)

    def __rmul__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rmul)

    def __truediv__(self, other: Any) -> Any:
        return self._arith_method(other, operator.truediv)

    def __rtruediv__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rtruediv)

    def __floordiv__(self, other: Any) -> Any:
        return self._arith_method(other, operator.floordiv)

    def __rfloordiv__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rfloordiv)

    def __mod__(self, other: Any) -> Any:
        return self._arith_method(other, operator.mod)

    def __rmod__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rmod)

    def __divmod__(self, other: Any) -> Any:
        return self._arith_method(other, divmod)

    def __rdivmod__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rdivmod)

    def __pow__(self, other: Any) -> Any:
        return self._arith_method(other, operator.pow)

    def __rpow__(self, other: Any) -> Any:
        return self._arith_method(other, roperator.rpow)
