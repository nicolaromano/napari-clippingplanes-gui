import pytest
from pytestqt import qtbot

from ..dock_widget import ImgClipperWidget
from ..widgets import ClippingSliderWidget

@pytest.fixture
def clipping_widget(qtbot: qtbot, make_napari_viewer):
    nv = make_napari_viewer()
    yield ImgClipperWidget(nv)

def test_clipping_widget(clipping_widget: ImgClipperWidget):
    assert len(clipping_widget.findChildren(ClippingSliderWidget)) == 3
