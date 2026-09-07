from handleguard.behaviours.base import StubDetector


class UnsafeSurfaceDetector(StubDetector):
    id = "B12"
    name = "unsafe_surface"
    config_key = "unsafe_surface"
