import pytest
from pytestqt import qtbot

from ..widgets import ClippingSliderWidget

# default values
name = 'TestSlider'


# slider fixture
@pytest.fixture
def clipping_slider(qtbot: qtbot):
    yield ClippingSliderWidget(name)


def test_clipping_slider(clipping_slider: ClippingSliderWidget):
    assert clipping_slider.name == name


def test_state_change(qtbot: qtbot, clipping_slider: ClippingSliderWidget):
    new_state = True

    def check_output(sout1, sout2):
        return all([sout1 == name, sout2 == new_state])

    with qtbot.waitSignal(clipping_slider.state_emitter, timeout=10, check_params_cb=check_output):
        clipping_slider.set_state(new_state)

    assert clipping_slider.state == new_state


def test_value_change(qtbot: qtbot, clipping_slider: ClippingSliderWidget):
    new_value = (10, 90)

    def check_output(sout1, sout2):
        return all([sout1 == name, sout2 == new_value])

    with qtbot.waitSignal(clipping_slider.value_emitter, timeout=10, check_params_cb=check_output):
        clipping_slider.set_value(new_value)

    assert clipping_slider.value == new_value


def test_range_change(qtbot: qtbot, clipping_slider: ClippingSliderWidget):
    new_range_min = 30
    new_range_max = 70

    def check_output(sout1, sout2):
        return all([sout1 == name, sout2 == (new_range_min, new_range_max)])

    with qtbot.waitSignal(clipping_slider.value_emitter, timeout=10, check_params_cb=check_output):
        clipping_slider.set_range(new_range_min, new_range_max)

    assert clipping_slider.range == (new_range_min, new_range_max)

