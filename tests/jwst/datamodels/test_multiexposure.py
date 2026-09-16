import numpy as np
import pytest

from stdatamodels.jwst import datamodels as dm


@pytest.mark.parametrize("model_type", [dm.ImageModel, dm.SlitModel, dm.SlitDataModel])
def test_multiexposure_model_from_datamodel(model_type):
    # Populate an input model with default arrays for everything in the schema
    shape = (2, 2)
    input_model = model_type(shape)
    input_model.meta.bunit_data = "MJy"
    populated_arrays = []
    for prop, val in input_model.schema["properties"].items():
        if "datatype" in val and not prop.startswith("int_times"):
            setattr(input_model, prop, input_model.get_default(prop))
            populated_arrays.append(prop)

    # Make a multi-exposure model from the input
    multi_model = dm.MultiExposureModel(input_model)

    # Make sure input arrays are populated in the first exposure
    for prop in populated_arrays:
        copied_array = getattr(multi_model.exposures[0], prop)
        np.testing.assert_allclose(copied_array, getattr(input_model, prop))

    # Top level meta should be copied to the new model
    assert multi_model.meta.bunit_data == "MJy"

    input_model.close()
    multi_model.close()
