import pytest

import joypad.input.worker as worker


def test_run_remap_worker_main_requires_profile():
    with pytest.raises(SystemExit) as exc:
        worker.run_remap_worker_main(["--pid", "1234"])
    assert exc.value.code == 2
