from handleguard.behaviours.base import StubDetector


class PalletOverhangDetector(StubDetector):
    id = "B08"
    name = "pallet_overhang"
    config_key = "pallet_overhang"
