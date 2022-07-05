from qtpy.QtWidgets import QWidget, QVBoxLayout

from utils import CPManager
from widgets import ClippingSliderWidget


class ImgClipperWidget(QWidget):
    """ImgClipperWidget for the napari viewer to control clipping planes.
    This widget is meant to be docked to the napari viewer window. It contains three ClippingSliderWidgets for separate
    control of each spatial dimension. Despite the image layer dimensions it will always have three sliders. This widget
    is only the GUI part of the napari_clippingplanes_gui for the underlying controller see:
    napari_clippingplanes_gui.utils.CPManager
    """
    def __init__(self, napari_viewer):
        """Initialise class instance

        :param napari_viewer: napari.Viewer to interact with
        :type napari_viewer: napari.Viewer
        """
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
