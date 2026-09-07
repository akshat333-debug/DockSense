from handleguard.behaviours.base import StubDetector


class UnsafeSequenceDetector(StubDetector):
    id = "B11"
    name = "unsafe_sequence"
    config_key = "unsafe_sequence"
