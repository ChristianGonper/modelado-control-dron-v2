import numpy as np

from simulador_quad.visualization.common import as_array


def test_as_array_returns_none_when_optional_field_is_fully_missing():
    samples = [
        {"time_s": 0.0, "state": {"position_W_m": [0.0, 0.0, 1.0]}},
        {"time_s": 1.0, "state": {"position_W_m": [1.0, 0.0, 1.0]}},
    ]

    assert as_array(samples, "desired_force_W_N", default=None) is None
    assert as_array(samples, "perturbation", "wind_W_m_s", default=None) is None


def test_as_array_pads_partial_optional_vector_fields():
    samples = [
        {"time_s": 0.0},
        {"time_s": 1.0, "perturbation": {"wind_W_m_s": [1.0, 2.0, 0.0]}},
        {"time_s": 2.0},
    ]

    wind = as_array(samples, "perturbation", "wind_W_m_s", default=None)

    assert wind is not None
    assert wind.shape == (3, 3)
    assert np.isnan(wind[0]).all()
    assert wind[1, 0] == 1.0
    assert np.isnan(wind[2]).all()