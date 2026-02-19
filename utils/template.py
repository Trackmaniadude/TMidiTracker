"""
Templating class. Instancing a template class will create a template which can make instances using the same input args.
Unfortunately typing didn't want to cooperate, so it's kind of jank.
The template wrapper intentionally lies about what its returning so the __init__ signature is kept, and the Templateable
class is simply to say that instantiate can be called.
Unfortunately, this means there is currently no way to say that only templates are allowed (to the type checker, Python knows
what it is).
"""

# This things gonna be some goof-ass code


from dataclasses import dataclass
from typing import Self


class Templateable:
    """Template classes must inherit this"""

    def instantiate(self, *args, **kwargs) -> Self:
        """Make an instance from this template. Supplied args/kwargs will override template args/kwargs"""
        return self


def template[C: type](cls: C) -> C:
    """Convert a class to a templated class. Templated classes will return nonfunctional templates when instantiated. The template will have
    an "instantiate()" function that can be called to create a new instance using the arguments given to the original.
    """

    class Template:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def instantiate(self, *args, **kwargs):
            a = list()

            for i in range(max(len(args), len(self.args))):
                if i < len(args):
                    a.append(args[i])
                else:
                    a.append(self.args[i])

            kwa = self.kwargs.copy()
            for k, v in kwargs.items():
                kwa[k] = v
            return cls(*a, **kwa)

        def __repr__(self) -> str:
            return f"Template<{cls.__name__}>"

    return Template  # type: ignore


if __name__ == "__main__":

    @template
    @dataclass
    class Test1(Templateable):
        a: int
        b: int
        c: int

    @template
    class Test2(Templateable):
        def __init__(self, d: int, e: int) -> None:
            self.d = d
            self.e = e

        def __str__(self) -> str:
            return f"Test2(d={self.d}, e={self.e})"

    t1 = Test1(1, 2, 3)
    q = t1.instantiate()
    print(t1)
    print(q)
    print(t1.instantiate())
    print(t1.instantiate())
    print(t1.instantiate())
    t2 = Test2(1, 2)
    print(t2)
    print(t2.instantiate())
    print(t2.instantiate())
    print(t2.instantiate())
