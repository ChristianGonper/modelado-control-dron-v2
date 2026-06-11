import matplotlib as mpl
import pytest

from simulador_quad.visualization.style import get_controller_style, use_style, COLORS


def test_get_controller_style():
    # Specific known controller
    style_pid = get_controller_style("classic_family_pid")
    assert style_pid["color"] == COLORS["pid"]
    assert style_pid["label"] == "PID Familiar"
    assert style_pid["linestyle"] == "-"

    # MLP neural controller
    style_mlp = get_controller_style("neural_outer_force_mlp")
    assert style_mlp["color"] == COLORS["mlp"]
    assert "MLP" in style_mlp["label"]

    # Frozen PID per family
    style_hold = get_controller_style("classic_pid_hold")
    assert style_hold["label"] == "PID Hold"
    assert style_hold["color"] == "#0072B2"

    # Dynamic classic transfer matching
    style_trans = get_controller_style("classic_transfer_lissajous")
    assert "Lissa" in style_trans["label"]
    assert style_trans["linestyle"] == ":"
    assert get_controller_style("classic_transfer_lissajous")["color"] == style_trans["color"]

    # Unknown fallback
    style_unknown = get_controller_style("some_random_controller")
    assert style_unknown["color"] == COLORS["secondary"]
    assert style_unknown["label"] == "some_random_controller"


def test_use_style_context():
    # Record original values
    orig_linewidth = mpl.rcParams.get("lines.linewidth")
    orig_fontsize = mpl.rcParams.get("font.size")
    orig_spines_top = mpl.rcParams.get("axes.spines.top")

    # Inside report context
    with use_style("report"):
        assert mpl.rcParams["font.family"] == ["serif"]
        assert "Latin Modern Roman" in mpl.rcParams["font.serif"]
        assert mpl.rcParams["lines.linewidth"] == 1.4
        assert mpl.rcParams["font.size"] == 9.0
        assert mpl.rcParams["axes.spines.top"] is False
        assert mpl.rcParams["axes.spines.right"] is False

    # Inside diagnostic context
    with use_style("diagnostic"):
        assert mpl.rcParams["font.family"] == ["serif"]
        assert mpl.rcParams["lines.linewidth"] == 1.5
        assert mpl.rcParams["font.size"] == 10.0

    # Restored to original
    assert mpl.rcParams.get("lines.linewidth") == orig_linewidth
    assert mpl.rcParams.get("font.size") == orig_fontsize
    assert mpl.rcParams.get("axes.spines.top") == orig_spines_top
