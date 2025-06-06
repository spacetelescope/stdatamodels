import gc
import warnings
import weakref

import pytest
import asdf
from asdf.exceptions import ValidationError
import numpy as np

from stdatamodels.exceptions import ValidationWarning
from models import BasicModel, FitsModel, ValidationModel, RequiredModel


class _DoesNotRaiseContext:
    """
    Dummy context manager for use in parametrized tests, for non-raising cases.
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        return "does_not_raise"


# Define a singleton to use
does_not_raise = _DoesNotRaiseContext()


def test_scalar_attribute_assignment():
    model = ValidationModel()

    assert model.meta.string_attribute is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.string_attribute = "foo"
    assert model.meta.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    assert model.meta.string_attribute == "foo"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.string_attribute = None
    assert model.meta.string_attribute is None


def test_object_attribute_assignment():
    model = ValidationModel()

    assert model.meta.object_attribute.string_attribute is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.object_attribute = {"string_attribute": "foo"}
    assert model.meta.object_attribute.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.object_attribute = "bar"
    assert model.meta.object_attribute.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.object_attribute = {"string_attribute": 42}
    assert model.meta.object_attribute.string_attribute == "foo"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.object_attribute = None
    assert model.meta.object_attribute.string_attribute is None


def test_list_attribute_ssignment():
    model = ValidationModel()

    assert len(model.meta.list_attribute) == 0
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.list_attribute.append({"string_attribute": "foo"})
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.list_attribute.append({"string_attribute": 42})
    assert len(model.meta.list_attribute) == 1
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.list_attribute = None
    assert len(model.meta.list_attribute) == 0


def test_object_assignment_with_nested_null():
    model = ValidationModel()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.object_attribute = {"string_attribute": None}


def test_validation_for_required(tmp_path):
    fn = tmp_path / "test.fits"
    model = RequiredModel()
    with pytest.raises(ValidationError, match="'required_attribute' is a required property"):
        model.save(fn)


@pytest.mark.parametrize(
    "init_value, env_value, passed",
    [
        (None, None, False),
        (True, None, True),
        (False, None, False),
        (None, "true", True),
        (None, "false", False),
    ],
)
def test_pass_invalid_values_attribute_assignment(monkeypatch, init_value, env_value, passed):
    if env_value is not None:
        monkeypatch.setenv("PASS_INVALID_VALUES", env_value)

    model = ValidationModel(pass_invalid_values=init_value)

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42

    if passed:
        assert model.meta.string_attribute == 42
    else:
        assert model.meta.string_attribute is None


@pytest.mark.parametrize(
    "suffix",
    [
        "asdf",
        "fits",
    ],
)
def test_pass_invalid_values_on_write(tmp_path, suffix):
    file_path = tmp_path / f"test.{suffix}"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42

    ctx = pytest.warns(ValidationWarning) if suffix == "asdf" else pytest.raises(ValidationError)
    with ctx:
        model.save(file_path)

    if suffix == "asdf":
        with asdf.open(file_path) as af:
            assert af["meta"]["string_attribute"] == 42


@pytest.mark.parametrize(
    "init_value, env_value, expected_context_manager",
    [
        (None, None, pytest.warns(ValidationWarning)),
        (True, None, pytest.raises(ValidationError)),
        (False, None, pytest.warns(ValidationWarning)),
        (None, "true", pytest.raises(ValidationError)),
        (None, "false", pytest.warns(ValidationWarning)),
    ],
)
def test_strict_validation_attribute_assignment(
    monkeypatch, init_value, env_value, expected_context_manager
):
    if env_value is not None:
        monkeypatch.setenv("STRICT_VALIDATION", env_value)

    model = ValidationModel(strict_validation=init_value)

    with expected_context_manager:
        model.meta.string_attribute = 42
    assert model.meta.string_attribute is None


def test_validate():
    model = ValidationModel(pass_invalid_values=True)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model.meta.string_attribute = "foo"
        model.validate()

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    assert model.meta.string_attribute == 42

    with pytest.warns(ValidationWarning):
        model.validate()


@pytest.mark.parametrize(
    "suffix",
    [
        "asdf",
        "fits",
    ],
)
def test_validation_on_write(tmp_path, suffix):
    file_path = tmp_path / f"test.{suffix}"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42

    # pass_invalid_values=True does not allow saving an invalid FITS file
    ctx = pytest.warns(ValidationWarning) if suffix == "asdf" else pytest.raises(ValidationError)

    with ctx:
        model.save(file_path)


@pytest.mark.parametrize(
    "init_value, env_value, expected_context_manager, string_attribute_value",
    [
        (None, None, pytest.warns(ValidationWarning), None),
        (True, None, pytest.warns(ValidationWarning), None),
        (False, None, does_not_raise, 42),
        (None, "true", pytest.warns(ValidationWarning), None),
        (None, "false", does_not_raise, 42),
    ],
)
def test_validate_on_assignment(
    monkeypatch, init_value, env_value, expected_context_manager, string_attribute_value
):
    if env_value is not None:
        monkeypatch.setenv("VALIDATE_ON_ASSIGNMENT", env_value)
    model = ValidationModel(validate_on_assignment=init_value)

    with expected_context_manager:
        model.meta.string_attribute = 42  # Bad assignment
    assert model.meta.string_attribute is string_attribute_value


@pytest.mark.parametrize(
    "init_value, warning_class, string_attribute_value",
    [
        (True, ValidationWarning, "bar"),
        (False, None, 42),
    ],
)
def test_validate_on_assignment_setitem(init_value, warning_class, string_attribute_value):
    model = ValidationModel(validate_on_assignment=init_value)

    # Check values assigned that are valid
    value = "foo"
    model.meta.list_attribute.append({"string_attribute": value})
    assert model.meta.list_attribute[0].string_attribute == value

    value2 = "bar"
    model.meta.list_attribute[0] = {"string_attribute": value2}
    assert model.meta.list_attribute[0].string_attribute == value2

    # Now check invalid assignments.  Currently string_attribute="bar".  Try
    # assigning an invalid type
    value3 = 42
    if warning_class is None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            model.meta.list_attribute[0] = {"string_attribute": value3}
    else:
        with pytest.warns(warning_class):
            model.meta.list_attribute[0] = {"string_attribute": value3}

    assert model.meta.list_attribute[0].string_attribute == string_attribute_value


@pytest.mark.parametrize(
    "validate_on_assignment, warning_class, string_attribute_value",
    [
        (True, ValidationWarning, "bar"),
        (False, None, 42),
    ],
)
def test_validate_on_assignment_insert(
    validate_on_assignment, warning_class, string_attribute_value
):
    model = ValidationModel(validate_on_assignment=validate_on_assignment)

    model.meta.list_attribute.insert(0, {"string_attribute": "bar"})
    assert model.meta.list_attribute[0].string_attribute == "bar"

    if warning_class is None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            model.meta.list_attribute.insert(0, {"string_attribute": 42})
    else:
        with pytest.warns(warning_class):
            model.meta.list_attribute.insert(0, {"string_attribute": 42})
    assert model.meta.list_attribute[0].string_attribute == string_attribute_value


# --------------------------------------------------------------------
# Validation flag interaction testing.

# This test is the same as one above, but with strict_validation=True.
# This ensures strict_validation=True doesn't effect this test.


@pytest.mark.parametrize(
    "validate_on_assignment, strict_validation, expected_context_manager, value",
    [
        (True, False, pytest.warns(ValidationWarning), None),
        (True, True, pytest.raises(ValidationError), None),
        (False, False, does_not_raise, 42),
        (False, True, does_not_raise, 42),
    ],
)
def test_validate_on_assignment_strict_validation(
    tmp_path, validate_on_assignment, strict_validation, expected_context_manager, value
):
    model = ValidationModel(
        validate_on_assignment=validate_on_assignment, strict_validation=strict_validation
    )

    with expected_context_manager:
        model.meta.string_attribute = 42
    assert model.meta.string_attribute is value


@pytest.mark.parametrize(
    "validate_on_assignment, pass_invalid_values, expected_context_manager, value",
    [
        (True, False, pytest.warns(ValidationWarning), None),
        (True, True, pytest.warns(ValidationWarning), 42),
        (False, False, does_not_raise, 42),
        (False, True, does_not_raise, 42),
    ],
)
def test_validate_on_assignment_pass_invalid_values(
    validate_on_assignment, pass_invalid_values, expected_context_manager, value
):
    model = ValidationModel(
        validate_on_assignment=validate_on_assignment, pass_invalid_values=pass_invalid_values
    )

    # pass_invalid_values=True allows for assignment,
    # even with validate_on_assignment=True
    with expected_context_manager:
        model.meta.string_attribute = 42  # Bad assignment
    assert model.meta.string_attribute == value


def test_ndarray_validation(tmp_path):
    file_path = tmp_path / "test.asdf"

    # Wrong dtype
    with asdf.AsdfFile() as af:
        af["data"] = np.ones((4, 4), dtype=np.float64)
        af.write_to(file_path)

    with pytest.raises(
        ValidationError, match="Array datatype 'float64' is not compatible with 'float32'"
    ):
        with BasicModel(file_path, strict_validation=True, validate_arrays=True) as model:
            model.validate()

    # Wrong dimensions
    with asdf.AsdfFile() as af:
        af["data"] = np.ones((4,), dtype=np.float32)
        af.write_to(file_path)

    with pytest.raises(ValidationError, match="Wrong number of dimensions: Expected 2, got 1"):
        with BasicModel(file_path, strict_validation=True, validate_arrays=True) as model:
            model.validate()


def test_ndarray_datatype_validation(tmp_path):
    file_path = tmp_path / "test.fits"
    m = FitsModel(validate_arrays=True)
    m.instance["data"] = np.ones((4, 4), dtype=np.float64)
    with pytest.raises(
        ValidationError, match="Array datatype 'float64' is not compatible with 'float32'"
    ):
        m.save(file_path)


def test_validation_memory_leak():
    """
    Test that assigning an array to a model and then overwriting
    the attribute with a new array doesn't result in the model keeping
    a reference to the assigned array.
    """
    # basic model validates `data` to be a float32 with 2 dimensions
    model = BasicModel()

    # get the default array
    original_array = model.data

    # make a new valid array
    new_array = np.ones_like(original_array)

    # assign it to the model
    model.data = new_array

    # grab a weakref to the new array
    new_array_ref = weakref.ref(new_array)

    # re-assign the original array
    model.data = original_array

    # delete the new array (which should no longer be linked to the model)
    del new_array

    # and collect garbage to free the array
    gc.collect()

    # verify that the weakref fails to resolve
    assert new_array_ref() is None
