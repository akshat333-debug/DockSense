from handleguard.behaviours.base import StubDetector


class ImproperStackDetector(StubDetector):
    id = "B05"
    name = "improper_stack"
    config_key = "improper_stack"
