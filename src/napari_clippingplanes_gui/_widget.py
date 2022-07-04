"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/plugins/stable/guides.html#widgets

Replace code below according to your needs.
"""
import numpy as np
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QLabel
from qtpy.QtCore import Qt, Signal, Slot
from superqt import QLabeledRangeSlider, QRangeSlider
from napari.layers import Image

Horizontal = Qt.Orientation.Horizontal


@Slot()
def print_signal(*message):
    print(message)


def get_spatial_bounds(layer):
    shape = layer.data.shape
    bounds = [(0, v) for i, v in enumerate(reversed(shape)) if i < 3]
    bounds.reverse()
    return bounds

class ClippingSliderWidget(QWidget):
    state_emitter = Signal([str, bool])
    value_emitter = Signal([str, tuple])

    def __init__(self, name, srange=(0, 100), value=(0, 100)):
        super().__init__()
        self.name = name
        self._init_ui()
        self.setRange(*srange)
        self.setValue(value)
        self.state = self.get_state()
        self.value = self.get_value()

    def _init_ui(self):
        self.active_check = QCheckBox()
        self.rangeslider = QRangeSlider(Horizontal)

        self.active_check.stateChanged.connect(self.stateChanged)
        self.rangeslider.valueChanged.connect(self.valueChanged)

        layout = QHBoxLayout()
        layout.addWidget(self.active_check)
        layout.addWidget(QLabel(self.name))
        layout.addWidget(self.rangeslider)
        self.setLayout(layout)

    def get_state(self):
        return self.active_check.isChecked()

    def set_state(self, state):
        self.active_check.setChecked(state)
        self.state = state

    def get_value(self):
        return self.rangeslider.value()

    def set_value(self, value):
        self.rangeslider.setValue(value)
        self.value = value

    def stateChanged(self):
        return self.state_emitter.emit(self.name, self.get_state())

    def valueChanged(self):
        return self.value_emitter.emit(self.name, self.get_value())

    def setRange(self, lower: float, upper: float):
        self.rangeslider.setRange(lower, upper)

    def setValue(self, value):
        self.rangeslider.setValue(value)
        self.valueChanged()


class CPManager:
    ref = dict(z=(0, 0), y=(2, 1), x=(4, 2))
    def __init__(self, viewer, sliders):
        super().__init__()
        self.viewer = viewer
        self.sliders = {}
        for slider in sliders:
            self._register_slider(slider)
        for layer in self.viewer.layers:
            if isinstance(layer, Image):
                self._layer_spawn_clipping_planes(layer)

    def _register_slider(self, slider):
        self.sliders[slider.name] = slider
        slider.state_emitter.connect(self.slider_state_changed)
        slider.value_emitter.connect(self.slider_value_changed)

    def _unregister_slider(self, slider_name):
        slider = self.sliders.pop(slider_name)
        slider.state_emitter.disconnect(self.slider_state_changed)
        slider.value_emitter.disconnect(self.slider_value_changed)

    def _layer_spawn_clipping_planes(self, layer):
        if not layer.experimental_clipping_planes:
            axis_bounds = get_spatial_bounds(layer)
            layer.metadata['cp_spacing'] = dict(
                x=np.linspace(*axis_bounds[2], num=101),
                y=np.linspace(*axis_bounds[1], num=101),
                z=np.linspace(*axis_bounds[0], num=101)
            )
            cpl = []
            for axn, (axis, bounds) in zip(('z', 'y', 'x'), enumerate(axis_bounds)):
                for ind, direction in enumerate((1, -1)):
                    position = np.zeros(3, dtype=int)
                    position[axis] = bounds[ind]
                    normal = np.zeros(3, dtype=int)
                    normal[axis] = direction
                    enabled = self.sliders[axn].state
                    cp_dict = dict(position=position, normal=normal, enabled=enabled)
                    cpl.append(cp_dict)
            layer.experimental_clipping_planes = cpl

    def slider_state_changed(self, name, state):
        for layer in self.viewer.layers:
            if isinstance(layer, Image) and layer.experimental_clipping_planes:
                layer.experimental_clipping_planes[self.ref[name][0]].enabled = state
                layer.experimental_clipping_planes[self.ref[name][0] + 1].enabled = state

    def slider_value_changed(self, name, crange):
        for layer in self.viewer.layers:
            if isinstance(layer, Image) and layer.experimental_clipping_planes:
                lower = np.zeros(3)
                lower[self.ref[name][1]] = layer.metadata['cp_spacing'][name][crange[0]]
                upper = np.zeros(3)
                upper[self.ref[name][1]] = layer.metadata['cp_spacing'][name][crange[1]]
                layer.experimental_clipping_planes[self.ref[name][0]].position = lower
                layer.experimental_clipping_planes[self.ref[name][0] + 1].position = upper


class ImgClipperWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self._init_ui()
        self.x_clipping_slider.set_state(True)
        self.clipping_plane_manager = CPManager(
            self.viewer, [self.x_clipping_slider, self.y_clipping_slider, self.z_clipping_slider]
        )

    def _init_ui(self):
        self.x_clipping_slider = ClippingSliderWidget(name='x')
        self.y_clipping_slider = ClippingSliderWidget(name='y')
        self.z_clipping_slider = ClippingSliderWidget(name='z')

        layout = QVBoxLayout()
        layout.addWidget(self.x_clipping_slider)
        layout.addWidget(self.y_clipping_slider)
        layout.addWidget(self.z_clipping_slider)
        self.setLayout(layout)
