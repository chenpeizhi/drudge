"""Drudge for SU(2) Lie algebra."""

import functools
import operator

from sympy import Integer

from .genquad import GenQuadDrudge
from .term import Vec
from .utils import sympy_key


class SU2LatticeDrudge(GenQuadDrudge):
    """Drudge for a lattice of SU(2) algebras.

    This drudge has the commutation rules for SU(2) algebras in Cartan-Weyl form
    (Ladder operators).  Here both the shift and Cartan operators can have
    additional *lattice indices*.  Operators on different lattice sites always
    commute.

    The the normal-ordering operation would try to put raising operators before
    the Cartan operators, which come before the lowering operators.

    """

    def __init__(
            self, ctx, cartan=Vec('J^z'), raise_=Vec('J^+'), lower=Vec('J^-'),
            root=Integer(1), norm=Integer(2),
            **kwargs
    ):
        """Initialize the drudge.

        Parameters
        ----------

        ctx
            The Spark context for the drudge.

        cartan
            The basis operator for the Cartan subalgebra (:math:`J^z` operator
            for spin problem).  It is registered in the name archive by the
            first letter in its label followed by an underscore.

        raise_
            The raising operator.  It is also also registered in the name
            archive by the first letter in its label followed by ``_p``.

        lower
            The lowering operator, registered by the first letter followed by
            ``_m``.

        root
            The coefficient for the commutator between the Cartan and shift
            operators.

        norm
            The coefficient for the commutator between the raising and lowering
            operators.

        All other keyword arguments are given to the base class
        :py:class:`GenQuadDrudge`.

        """
        super().__init__(ctx, **kwargs)

        self.cartan = cartan
        self.raise_ = raise_
        self.lower = lower
        self.set_name(**{
            cartan.label[0] + '_': cartan,
            raise_.label[0] + '_p': raise_,
            lower.label[0] + '_m': lower
        })

        self._root = root
        self._norm = norm

        self._swapper = functools.partial(
            _swap_su2, cartan=cartan, raise_=raise_, lower=lower,
            root=root, norm=norm
        )

    def swapper(self) -> GenQuadDrudge.Swapper:
        """The swapper for the spin algebra."""
        return self._swapper


def _swap_su2(
        vec1: Vec, vec2: Vec, *,
        cartan, raise_, lower, root, norm
):
    """Swap two vectors based on the SU2 rules.
    """

    char1, indice1, key1 = _parse_vec(vec1, cartan, raise_, lower)
    char2, indice2, key2 = _parse_vec(vec2, cartan, raise_, lower)
    if len(indice1) != len(indice2):
        raise ValueError(
            'Invalid SU2 generators on lattice', (vec1, vec2),
            'incompatible number of lattice indices'
        )
    delta = functools.reduce(
        operator.mul, zip(indice1, indice2), _UNITY
    )

    if char1 == _RAISE:

        if char2 == _RAISE:
            if key1 < key2:
                return None
            elif key1 > key2:
                return _UNITY, _NOUGHT
            else:
                return _NOUGHT, _NOUGHT  # They are nilpotent.
        else:
            return None

    elif char1 == _CARTAN:

        if char2 == _RAISE:
            return _UNITY, root * delta * vec2
        elif char2 == _CARTAN:
            if key1 > key2:
                return _UNITY, _NOUGHT
            else:
                return None
        else:
            return None

    elif char1 == _LOWER:

        if char2 == _RAISE:
            return _UNITY, - norm * delta * cartan[indice1]
        elif char2 == _CARTAN:
            return _UNITY, root * delta * vec1
        else:
            if key1 < key2:
                return None
            elif key1 > key2:
                return _UNITY, _NOUGHT
            else:
                return _NOUGHT, _NOUGHT

    else:
        assert False


_RAISE = 0
_CARTAN = 1
_LOWER = 2


def _parse_vec(vec, cartan, raise_, lower):
    """Get the character and lattice indices, and indices keys of the vector.
    """

    base = vec.base
    if base == cartan:
        char = _CARTAN
    elif base == raise_:
        char = _RAISE
    elif base == lower:
        char = _LOWER
    else:
        raise ValueError('Unexpected vector for SU2 algebra', vec)

    indices = vec.indices
    keys = tuple(sympy_key(i) for i in indices)

    return char, indices, keys


_UNITY = Integer(1)
_NOUGHT = Integer(0)
