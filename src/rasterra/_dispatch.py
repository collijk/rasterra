from typing import Any

import numpy as np

from rasterra._typing import NumpyUFuncMethod

DISPATCHED_UFUNCS = {
    "add",
    "sub",
    "mul",
    "pow",
    "mod",
    "floordiv",
    "truediv",
    "divmod",
    "eq",
    "ne",
    "lt",
    "gt",
    "le",
    "ge",
    "matmul",
    "and",
    "or",
    "xor",
    "neg",
    "pos",
    "abs",
}
UNARY_UFUNCS = {
    "abs",
    "neg",
    "pos",
}
UFUNC_ALIASES = {
    "subtract": "sub",
    "multiply": "mul",
    "floor_divide": "floordiv",
    "true_divide": "truediv",
    "power": "pow",
    "remainder": "mod",
    "divide": "truediv",
    "equal": "eq",
    "not_equal": "ne",
    "less": "lt",
    "greater": "gt",
    "less_equal": "le",
    "greater_equal": "ge",
    "bitwise_and": "and",
    "bitwise_or": "or",
    "bitwise_xor": "xor",
    "negative": "neg",
    "positive": "pos",
    "absolute": "abs",
}
REVERSED_NAMES = {
    "lt": "__gt__",
    "gt": "__lt__",
    "le": "__ge__",
    "ge": "__le__",
    "eq": "__eq__",
    "ne": "__ne__",
}
REDUCTION_ALIASES = {
    "maximum": "max",
    "minimum": "min",
    "add": "sum",
    "multiply": "prod",
}


def not_implemented(*args, **kwargs):
    return NotImplemented


def maybe_dispatch_ufunc_to_dunder_op(
    object_: Any,
    ufunc: np.ufunc,
    method: NumpyUFuncMethod,
    *inputs,
    **kwargs,
) -> Any:
    """Dispatches a numpy ufunc to a dunder method.

    Parameters
    ----------
    object_
        The object to dispatch to.
    ufunc
        The ufunc to dispatch.
    method
        One of "reduce", "accumulate", "reduceat", "outer", "at", "__call__".
    *inputs
        The inputs to the ufunc.
    **kwargs
        The keyword arguments to the ufunc.

    Returns
    -------
    Any
        The result of the dispatch.

    """
    if kwargs or ufunc.nin > 2:
        return NotImplemented

    op_name = ufunc.__name__
    op_name = UFUNC_ALIASES.get(op_name, op_name)

    if method == "__call__" and op_name in DISPATCHED_UFUNCS:
        if inputs[0] is object_:
            name = f"__{op_name}__"
            meth = getattr(object_, name, not_implemented)

            if op_name in UNARY_UFUNCS:
                assert len(inputs) == 1
                return meth()
            else:
                assert len(inputs) == 2
                return meth(inputs[1])

        elif inputs[1] is object_:
            name = REVERSED_NAMES.get(op_name, f"__r{op_name}__")
            meth = getattr(object_, name, not_implemented)
            return meth(inputs[0])

        else:
            return NotImplemented

    else:
        return NotImplemented


def dispatch_ufunc_with_out(
    object_: Any,
    ufunc: np.ufunc,
    method: NumpyUFuncMethod,
    *inputs,
    **kwargs,
) -> Any:
    out = kwargs.pop("out")
    where = kwargs.pop("where", None)

    result = getattr(ufunc, method)(*inputs, **kwargs)

    if result is NotImplemented:
        return NotImplemented

    if isinstance(result, tuple):
        # i.e. np.divmod, np.modf, np.frexp
        if not isinstance(out, tuple) or len(out) != len(result):
            raise NotImplementedError

        for arr, res in zip(out, result):
            _assign_where(arr, res, where)

        return out

    if isinstance(out, tuple):
        if len(out) == 1:
            out = out[0]
        else:
            raise NotImplementedError

    _assign_where(out, result, where)
    return out


def dispatch_reduction_ufunc(
    object_: Any,
    ufunc: np.ufunc,
    method: NumpyUFuncMethod,
    *inputs,
    **kwargs,
) -> Any:
    if len(inputs) != 1 or inputs[0] is not object_:
        return NotImplemented

    if ufunc.__name__ not in REDUCTION_ALIASES:
        return NotImplemented

    method_name = REDUCTION_ALIASES[ufunc.__name__]

    if not hasattr(object_, method_name):
        return NotImplemented

    return getattr(object_, method_name)(**kwargs)


def _assign_where(out, result, where):
    if where is None:
        out[:] = result
    else:
        np.putmask(out, where, result)
