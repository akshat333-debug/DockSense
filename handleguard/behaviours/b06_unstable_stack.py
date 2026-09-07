from handleguard.behaviours.base import StubDetector


class UnstableStackDetector(StubDetector):
    id = "B06"
    name = "unstable_stack"
    config_key = "unstable_stack"
