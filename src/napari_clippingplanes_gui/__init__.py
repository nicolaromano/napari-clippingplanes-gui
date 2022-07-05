
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .dock_widget import ImgClipperWidget
from .widgets import ClippingSliderWidget
