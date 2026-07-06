# SPDX-License-Identifier: MIT
import claude_session_exporter


def test_version_exposed():
    assert claude_session_exporter.__version__ == "0.1.0"
