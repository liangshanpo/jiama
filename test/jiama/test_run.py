import os
import signal
import subprocess

import pytest


def test_run():
    test_dir = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))
    cmd = f'jiama run jiama.sample --config {test_dir}/config.toml &'
    p = subprocess.Popen(cmd, shell=True)
    assert os.getpid()

    os.killpg(os.getpgid(p.pid), signal.SIGTERM)


if __name__ == '__main__':
    pytest.main(['-s', '-q'])
