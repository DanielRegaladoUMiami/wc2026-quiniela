"""Sanity tests for RPS implementation against published reference values."""

import numpy as np

from src.eval.rps import log_loss_1x2, mean_rps, outcome_1x2, rps


def test_rps_perfect_prediction():
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    outcomes = np.array([0, 1, 2])
    assert mean_rps(probs, outcomes) == 0.0


def test_rps_uniform_baseline():
    # Uniform forecast on 1X2:
    #   outcome 0 (home win) or 2 (away win) -> RPS = 5/18
    #   outcome 1 (draw)                     -> RPS = 1/9
    probs = np.array([[1 / 3, 1 / 3, 1 / 3]])
    assert abs(rps(probs, np.array([0]))[0] - 5 / 18) < 1e-9
    assert abs(rps(probs, np.array([1]))[0] - 1 / 9) < 1e-9
    assert abs(rps(probs, np.array([2]))[0] - 5 / 18) < 1e-9


def test_rps_constantinou_example():
    # From Constantinou & Fenton 2012 worked example:
    # forecast (0.5, 0.25, 0.25), outcome home win -> RPS = 0.15625
    probs = np.array([[0.5, 0.25, 0.25]])
    assert abs(rps(probs, np.array([0]))[0] - 0.15625) < 1e-9


def test_log_loss_perfect():
    probs = np.array([[0.999999, 0.0000005, 0.0000005]])
    assert log_loss_1x2(probs, np.array([0])) < 1e-5


def test_outcome_1x2():
    assert outcome_1x2(2, 1) == 0
    assert outcome_1x2(1, 1) == 1
    assert outcome_1x2(0, 3) == 2
