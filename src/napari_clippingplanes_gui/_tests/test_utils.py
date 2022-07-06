import numpy as np
import pytest

from ..utils import get_spatial_bounds, CPManager
from ..widgets import ClippingSliderWidget

# viewer fixture
@pytest.fixture
def viewer(make_napari_viewer):
    nv = make_napari_viewer()
    nv.add_image(np.zeros((100, 100)), name='2D', metadata=dict(bounds=[(0, 100), (0, 100)]))
    nv.add_image(np.zeros((10, 100, 100)), name='3D', metadata=dict(bounds=[(0, 10), (0, 100), (0, 100)]))
    nv.add_image(np.zeros((10, 10, 100, 100)), name='4D', metadata=dict(bounds=[(0, 10), (0, 100), (0, 100)]))
    nv.add_labels(np.zeros((10, 100, 100), dtype=int), name='labels', metadata=dict(bounds=[(0, 10), (0, 100), (0, 100)]))
    return nv


@pytest.fixture
def cpmanager(viewer):
    sliders = [ClippingSliderWidget('x'), ClippingSliderWidget('y'), ClippingSliderWidget('z')]
    sliders[0].set_state(True)
    ref = dict(z=(0, 0), y=(2, 1), x=(4, 2))
    return CPManager(viewer, ref, sliders)


def test_get_spatial_bounds(viewer):
    for layer in viewer.layers:
        assert get_spatial_bounds(layer) == layer.metadata['bounds']


def test_cpmanager(cpmanager: CPManager):
    assert list(cpmanager.ref.keys()) == ['z', 'y', 'x']
    assert list(cpmanager.ref.values()) == [(0, 0), (2, 1), (4, 2)]


def test_un_register_slider(cpmanager: CPManager):
    # first unregister one of the sliders
    slider = cpmanager._unregister_slider('x')
    assert slider.name == 'x'
    assert 'x' not in cpmanager.sliders.keys()
    assert slider.receivers(slider.state_emitter) == 0
    assert slider.receivers(slider.value_emitter) == 0
    # now reregister the slider
    cpmanager._register_slider(slider)
    assert cpmanager.sliders['x'] == slider
    assert slider.receivers(slider.state_emitter) == 1
    assert slider.receivers(slider.value_emitter) == 1


def test_layer_spawn_clipping_planes(cpmanager: CPManager):
    ref_cpp_pos_norm_en = [
        ((0, 0, 0), (1, 0, 0), False),
        ((10, 0, 0), (-1, 0, 0), False),
        ((0, 0, 0), (0, 1, 0), False),
        ((0, 100, 0), (0, -1, 0), False),
        ((0, 0, 0), (0, 0, 1), True),
        ((0, 0, 100), (0, 0, -1), True),
    ]
    layers = {layer.name: layer.experimental_clipping_planes for layer in cpmanager.viewer.layers}
    assert not any([layers['2D'], layers['labels']])
    assert all([len(layers['3D']) == 6, len(layers['4D']) == 6])
    # 3D
    cpp_pos_norm_en = [(cpp.position, cpp.normal, cpp.enabled) for cpp in layers['3D']]
    for pos_norm_en, rpos_rnorm_ren in zip(cpp_pos_norm_en, ref_cpp_pos_norm_en):
        assert pos_norm_en == rpos_rnorm_ren
    # 4D
    cpp_pos_norm_en = [(cpp.position, cpp.normal, cpp.enabled) for cpp in layers['4D']]
    for pos_norm_en, rpos_rnorm_ren in zip(cpp_pos_norm_en, ref_cpp_pos_norm_en):
        assert pos_norm_en == rpos_rnorm_ren


def test_slider_state_changed(cpmanager: CPManager):
    sliders = cpmanager.sliders
    layers = {layer.name: layer.experimental_clipping_planes for layer in cpmanager.viewer.layers}
    sliders['y'].set_state(True)
    sliders['z'].set_state(True)
    assert all([
        cpp.enabled
        for key in ['3D', '4D']
        for cpp in layers[key]
    ])


def test_slider_value_changed(cpmanager: CPManager):
    sliders = cpmanager.sliders
    layers = {
        layer.name: layer.experimental_clipping_planes
        for layer in cpmanager.viewer.layers
    }
    sliders['y'].set_value((10, 20))
    sliders['z'].set_value((2, 4))
    new_positions = [(0.2, 0, 0), (0.4, 0, 0), (0, 10, 0), (0, 20, 0)]
    assert all([
        cpp.position == new_position
        for key in ['3D', '4D']
        for cpp, new_position in zip(layers[key], new_positions)
    ])

def test_layer_inserted(cpmanager: CPManager):
    viewer = cpmanager.viewer
    viewer.add_image(np.random.random((10, 100, 100)), name='new_image')
    viewer.add_labels(np.random.randint(0, 10, size=(10, 100, 100)), name='new_labels')
    assert viewer.layers['new_image'].experimental_clipping_planes
    assert not viewer.layers['new_labels'].experimental_clipping_planes
