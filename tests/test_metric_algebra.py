"""Unit test for the supplied DTI decomposition (competition page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)."""

from __future__ import annotations


def dti_from_parts(T: float, S: float, M: float, G: int) -> float:
    denominator = 0.2 * T + 0.2 * (S - M) + 0.8 * abs(G)
    return T / denominator if denominator else 0.0


def test_dti_algebra_matches_component_formula() -> None:
    # Synthetic values only: T=.5, S=1, M=.5, |G|=2 -> denominator 1.8.
    assert dti_from_parts(T=0.5, S=1.0, M=0.5, G=2) == 0.5 / 1.8


def test_isolated_unit_dot_has_zero_credit_until_kernel_credit_is_positive() -> None:
    # No credit: T=M=0, one prediction and one truth; introducing kernel credit raises DTI.
    no_credit = dti_from_parts(T=0.0, S=1.0, M=0.0, G=1)
    positive_credit = dti_from_parts(T=0.25, S=1.0, M=0.25, G=1)
    assert no_credit == 0.0
    assert positive_credit > no_credit


def test_exact_catalogue_pixel_is_excluded_from_non_catalogue_truth_term() -> None:
    # For a matched unit prediction, T=M=S=G=1 -> DTI=1.0.
    assert dti_from_parts(T=1.0, S=1.0, M=1.0, G=1) == 1.0
