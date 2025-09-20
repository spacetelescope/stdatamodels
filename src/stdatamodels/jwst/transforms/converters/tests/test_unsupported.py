import pytest

import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.transforms.converters.jwst_models import UnsupportedConverterError

"""Test attempting to load or save files with transforms that are no longer supported."""


@pytest.fixture
def model_with_unsupported_transform(tmp_path):
    asdf_file = """#ASDF 1.0.0
#ASDF_STANDARD 1.6.0
%YAML 1.1
%TAG ! tag:stsci.edu:asdf/
--- !core/asdf-1.1.0
model: !<tag:stsci.edu:jwst_pipeline/v23tosky-0.7.0>
  angles: [-0.0193, -0.1432, -0.04, -65.60, 273.089]
  axes_order: zyxyz
...
    """
    path = tmp_path / "model_with_unsupported_transform.asdf"
    path.write_text(asdf_file)
    return path


def test_load_unsupported_transform(model_with_unsupported_transform):
    """Test that loading a file with an unsupported transform raises the expected error."""
    with pytest.raises(
        UnsupportedConverterError,
    ):
        dm.open(model_with_unsupported_transform)
