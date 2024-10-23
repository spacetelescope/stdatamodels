import os
import sys

from stdatamodels.jwst._kwtool import cli


def test_cli(monkeypatch, tmp_path_factory, fake_kwd_path, limit_dmd_models):
    # move to a new, empty directory
    temp_cwd = tmp_path_factory.mktemp("cwd")
    os.chdir(temp_cwd)

    output_dir = tmp_path_factory.mktemp("output")
    output_path = output_dir / "my_report.html"

    monkeypatch.setattr(sys, "argv", [sys.argv[0], str(fake_kwd_path), "-o", str(output_path)])

    cli._from_cmdline()

    # make sure we didn't write out any local files
    assert not os.listdir(temp_cwd)

    # and that our output file exists
    assert output_path.exists()
