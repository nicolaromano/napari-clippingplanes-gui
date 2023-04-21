import numpy as np

from typing import Any, Dict, List, Tuple

from .widgets import ClippingSliderWidget


def get_spatial_bounds(layer) -> List[Tuple[int, Any]]:
    """Extract the border coordinates of an napari layer.
    
    :param layer: napari layer
    :type layer: napari.layers.Layer
    :return: list of coordinate tuples
    :rtype: List[Tuple[int, Any]]
    """
    shape = layer.data.shape
    bounds = [(0, v) for i, v in enumerate(reversed(shape)) if i < 3]
    bounds.reverse()
    return bounds


class CPManager:
    """Manager class for napari clipping planes and corresponding slider widgets.
    Manages the construction of clipping planes per image layer and the signal processing.
    """
    def __init__(self, viewer, ref: Dict, sliders: List[ClippingSliderWidget]):
        """Initialise class instance.

        :param viewer: napari viewer object to interact with
        :type viewer: napari.Viewer
        :param ref: reference dictionary to connect slider string ids with indices, keys must match slider names
        :type ref: Dict
        :param sliders: list of slider widgets to control the clipping planes
        :type sliders: napari_clippingplanes_gui.ClippingSliderWidget
        """
        super().__init__()
        self.viewer = viewer
        self.ref = ref
        self.sliders = {}
        for slider in sliders:
            self._register_slider(slider)
        for layer in self.viewer.layers:
            if layer._type_string in ['image', 'labels']:
                self._layer_spawn_clipping_planes(layer)

        assert self.sliders.keys() == self.ref.keys()

        self.viewer.layers.events.inserted.connect(self.layer_inserted)

    def _register_slider(self, slider: ClippingSliderWidget):
        """Register a slider widget to a CPManager instance.
        This method adds a slider widget to the internal dict of widgets and connects the slider widget signals to the
        matching slots.

        :param slider: slider widget instance
        :type slider: ClippingSliderWidget
        """
        self.sliders[slider.name] = slider
        slider.state_emitter.connect(self.slider_state_changed)
        slider.value_emitter.connect(self.slider_value_changed)

    def _unregister_slider(self, slider_name: str) -> ClippingSliderWidget:
        """Unregister a slider widget from a CPManager instance.
        This method removes a slider widget from the internal dict of widgets and disconnects the slider widget signals.

        :param slider_name: key for the internal slider dict, returns a registered slider
        :type slider_name: str
        :return: the unregistered slider for removal at other places
        :rtype: ClippingSliderWidget
        """
        slider = self.sliders.pop(slider_name)
        slider.state_emitter.disconnect(self.slider_state_changed)
        slider.value_emitter.disconnect(self.slider_value_changed)
        return slider

    def _layer_spawn_clipping_planes(self, layer):
        """Generate clipping planes for a napari viewer layer.
        The clipping planes will be first generated in form of dictionaries for each spatial axis (x, y, z) of the layer.
        The dictionaries are then send to layer.experimental_clipping_planes for object creation.

        :param layer: napari viewer layer for which clipping planes shall be generated
        :type layer: napari.layers.Layer
        """
        if not layer.experimental_clipping_planes and layer.ndim > 2:
            axis_bounds = get_spatial_bounds(layer)
            layer.metadata['cp_spacing'] = {
                key: np.linspace(*bounds, num=101)
                for key, bounds in zip(['z', 'y', 'x'], axis_bounds)
            }
            cpl = []
            for axn, (axis, bounds) in zip(('z', 'y', 'x'), enumerate(axis_bounds)):
                for ind, direction in enumerate((1, -1)):
                    position = np.zeros(3, dtype=int)
                    position[axis] = bounds[ind]
                    position = layer.data_to_world(position)
                    if len(position) > 3:
                        position = position[-3:]
                    normal = np.zeros(3, dtype=int)
                    normal[axis] = direction
                    enabled = self.sliders[axn].state
                    cp_dict = dict(
                        position=position,
                        normal=normal,
                        enabled=enabled
                    )
                    cpl.append(cp_dict)
            layer.experimental_clipping_planes = cpl

    def slider_state_changed(self, name: str, state: bool):
        """Callback for slider state_changed signals.
        A sent signal will result in enabling/disabling of the corresponding clipping planes of all viewer image layers.

        :param name: axis name (x, y, z)
        :type name: str
        :param state: new state of the connected slider (True / False)
        :type state: bool
        """
        for layer in self.viewer.layers:
            if layer._type_string == 'image' and layer.experimental_clipping_planes:
                layer.experimental_clipping_planes[self.ref[name][0]].enabled = state
                layer.experimental_clipping_planes[self.ref[name][0] + 1].enabled = state

    def slider_value_changed(self, name: str, crange: Tuple[int, int]):
        """Callback for slider value_changed signals.
        A sent signal will result in repositioning of the corresponding clipping planes of all viewer image layers.

        :param name: axis name (x, y, z)
        :type name: str
        :param crange: clipping range, the position of the "lower" and "upper" clipping plane
        :type crange: Tuple[int, int]
        """
        for layer in self.viewer.layers:
            if layer._type_string == ['image', 'labels'] and layer.experimental_clipping_planes:
                lower = np.zeros(3)
                lower[self.ref[name][1]] = layer.metadata['cp_spacing'][name][crange[0]]
                lower = layer.data_to_world(lower)
                if len(lower) > 3:
                    lower = lower[-3:]
                upper = np.zeros(3)
                upper[self.ref[name][1]] = layer.metadata['cp_spacing'][name][crange[1]]
                upper = layer.data_to_world(upper)
                if len(upper) > 3:
                    upper = upper[-3:]
                layer.experimental_clipping_planes[self.ref[name][0]].position = lower
                layer.experimental_clipping_planes[self.ref[name][0] + 1].position = upper

    def layer_inserted(self, event):
        """Callback for napari.Viewer.layers.events.inserted signals.
        A sent signal will start the _layer_spawn_clipping_planes method for a newly added layer. The new layer is
        extracted from the event source.

        :param event: napari event object, containing the event source
        :type event: napari.utils.events.Event
        """
        layer = event.source[-1]
        if layer._type_string in ['image', 'labels']:
            self._layer_spawn_clipping_planes(layer)
