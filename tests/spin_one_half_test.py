"""Tests for the drudges with explicit one-half spin."""

import pytest
from sympy import IndexedBase, symbols, Rational, KroneckerDelta

from drudge import (
    CR, AN, UP, DOWN, SpinOneHalfGenDrudge, SpinOneHalfPartHoleDrudge,
    RestrictedPartHoleDrudge
)


@pytest.fixture(scope='module')
def genmb(spark_ctx):
    """The fixture with a general spin one-half drudge."""
    return SpinOneHalfGenDrudge(spark_ctx)


def test_spin_one_half_general_drudge_has_properties(genmb):
    """Test the basic properties of the drudge."""

    dr = genmb

    assert dr.spin_vals == [UP, DOWN]
    assert dr.orig_ham.n_terms == 2 + 4
    assert dr.ham.n_terms == 2 + 3


def test_restricted_hf_theory(genmb):
    """Test the derivation of restricted HF theory."""

    dr = genmb
    p = dr.names

    c_dag = p.c_dag
    c_ = p.c_
    a, b, c, d = p.L_dumms[:4]
    alpha = symbols('alpha')

    # Concrete summation.
    rot = dr.sum(
        (alpha, [UP, DOWN]), Rational(1, 2) * c_dag[a, alpha] * c_[b, alpha]
    )

    comm = (dr.ham | rot).simplify()

    # Restricted theory has same density for spin up and down.
    rho = IndexedBase('rho')
    res = comm.eval_vev(lambda op1, op2, _: (
        rho[op2.indices[1], op1.indices[1]]
        if op1.indices[0] == CR and op2.indices[0] == AN
           and op1.indices[2] == op2.indices[2]
        else 0
    )).simplify()

    # The expected result.
    t = dr.one_body
    u = dr.two_body

    f = IndexedBase('f')
    expected = dr.einst(rho[b, c] * f[c, a] - f[b, c] * rho[c, a])
    expected = expected.subst(f[a, b], dr.einst(
        t[a, b] +
        2 * u[a, c, b, d] * rho[d, c] - u[c, a, b, d] * rho[d, c]
    ))
    expected = expected.simplify()

    assert res == expected


@pytest.fixture(scope='module')
def parthole(spark_ctx):
    """The fixture with a particle-hole spin one-half drudge."""
    return SpinOneHalfPartHoleDrudge(spark_ctx)


def test_spin_one_half_particle_hole_drudge_has_basic_properties(parthole):
    """Test basic properties of spin one-half particle-hole drudge."""

    dr = parthole
    p = dr.names

    assert dr.orig_ham.n_terms == 8 + 4 * 2 ** 4

    ham_terms = dr.ham.local_terms
    # Numbers are from the old PySLATA code.
    assert len([i for i in ham_terms if len(i.vecs) == 2]) == 8
    assert len([i for i in ham_terms if len(i.vecs) == 4]) == 36
    assert dr.ham.n_terms == 8 + 36


@pytest.fixture(scope='module')
def restricted_parthole(spark_ctx):
    """The fixture with a restricted particle-hole drudge."""
    return RestrictedPartHoleDrudge(spark_ctx)


def test_restricted_parthole_drudge_has_good_hamiltonian(restricted_parthole):
    """Test Hamiltonian of restricted particle-hole drudge.

    Here the original Hamiltonian is going to be compared with the Hamiltonian
    written in terms of the unitary group generators.
    """

    dr = restricted_parthole
    p = dr.names

    e_ = p.e_
    h = dr.one_body
    v = dr.two_body
    half = Rational(1, 2)
    orbs = tuple(dr.orb_ranges)
    p, q, r, s = symbols('p q r s')

    expected_ham = dr.sum(
        (p, orbs), (q, orbs), h[p, q] * e_[p, q]
    ) + dr.sum(
        (p, orbs), (q, orbs), (r, orbs), (s, orbs),
        half * v[p, r, q, s] * (
            e_[p, q] * e_[r, s] - KroneckerDelta(q, r) * e_[p, s]
        )
    )
    assert (dr.orig_ham - expected_ham).simplify() == 0
