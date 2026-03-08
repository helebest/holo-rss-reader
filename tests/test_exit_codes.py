from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import exit_codes


def test_from_error_kind_maps_all_known_values():
    assert exit_codes.from_error_kind("network") == exit_codes.NETWORK_ERROR
    assert exit_codes.from_error_kind("parse") == exit_codes.PARSE_ERROR
    assert exit_codes.from_error_kind("storage") == exit_codes.STORAGE_ERROR
    assert exit_codes.from_error_kind("validation") == exit_codes.PARAM_ERROR
    assert exit_codes.from_error_kind("unknown") == exit_codes.NETWORK_ERROR
