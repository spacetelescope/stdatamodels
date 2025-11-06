import asdf
import pytest
from asdf.exceptions import AsdfConversionWarning

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
meta:
  model_type: JwstDataModel
model: !<tag:stsci.edu:jwst_pipeline/v23tosky-0.7.0>
  angles: [-0.0193, -0.1432, -0.04, -65.60, 273.089]
  axes_order: zyxyz
...
    """
    path = tmp_path / "model_with_unsupported_transform.asdf"
    path.write_text(asdf_file)
    return path


def test_load_unsupported(model_with_unsupported_transform):
    """Test that loading a file with an unsupported transform raises the expected error."""
    with pytest.raises(
        UnsupportedConverterError,
    ):
        dm.open(model_with_unsupported_transform)


@pytest.mark.skipif(
    asdf.__version__ < "5.1.0",
    reason="warn_on_failed_conversion requires asdf>=5.1.0",
)
def test_load_unsupported_with_flag(model_with_unsupported_transform):
    """Test loading same file with the warning flag set raises a warning instead."""
    asdf.get_config().warn_on_failed_conversion = True
    with pytest.warns(AsdfConversionWarning):
        model = dm.open(model_with_unsupported_transform)

    # check that the transform is a serialized form of its inputs
    assert model.model.angles == [-0.0193, -0.1432, -0.04, -65.60, 273.089]
    assert model.model.axes_order == "zyxyz"
