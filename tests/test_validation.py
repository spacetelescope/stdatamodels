import pytest

import asdf
import numpy as np
from numpy.testing import assert_array_equal
from jsonschema import ValidationError

from stdatamodels.validate import ValidationWarning

from models import ValidationModel, FitsRequiredModel, RequiredModel


def test_scalar_attribute_assignment():
    model = ValidationModel()

    assert model.meta.string_attribute is None
    with pytest.warns(None) as warnings:
        model.meta.string_attribute = "foo"
    assert len(warnings) == 0
    assert model.meta.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    assert model.meta.string_attribute == "foo"

    with pytest.warns(None) as warnings:
        model.meta.string_attribute = None
    assert len(warnings) == 0
    assert model.meta.string_attribute is None


def test_object_attribute_assignment():
    model = ValidationModel()

    assert model.meta.object_attribute.string_attribute is None
    with pytest.warns(None) as warnings:
        model.meta.object_attribute = {"string_attribute": "foo"}
    assert len(warnings) == 0
    assert model.meta.object_attribute.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.object_attribute = "bar"
    assert model.meta.object_attribute.string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.object_attribute = {"string_attribute": 42}
    assert model.meta.object_attribute.string_attribute == "foo"

    with pytest.warns(None) as warnings:
        model.meta.object_attribute = None
    assert len(warnings) == 0
    assert model.meta.object_attribute.string_attribute is None


def test_list_attribute_ssignment():
    model = ValidationModel()

    assert len(model.meta.list_attribute) == 0
    with pytest.warns(None) as warnings:
        model.meta.list_attribute.append({"string_attribute": "foo"})
    assert len(warnings) == 0
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.list_attribute.append({"string_attribute": 42})
    assert len(model.meta.list_attribute) == 1
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with pytest.warns(None) as warnings:
        model.meta.list_attribute = None
    assert len(warnings) == 0
    assert len(model.meta.list_attribute) == 0


@pytest.mark.xfail(reason="validation of a required attribute not yet implemented", strict=True)
def test_required_attribute_assignment():
    model = RequiredModel()

    with pytest.warns(None) as warnings:
        model.meta.required_attribute = "foo"

    with pytest.warns(ValidationWarning):
        model.meta.required_attribute = None


def test_fits_required_attribute_assignment():
    model = FitsRequiredModel()

    with pytest.warns(None) as warnings:
        model.meta.required_keyword = "foo"
    assert len(warnings) == 0
    assert model.meta.required_keyword == "foo"

    with pytest.warns(ValidationWarning, match="REQKWRD is a required value"):
        model.meta.required_keyword = None
    assert model.meta.required_keyword == "foo"

    with pytest.warns(None) as warnings:
        model.required_hdu = np.zeros((2, 2))
    assert len(warnings) == 0
    assert_array_equal(model.required_hdu, np.zeros((2, 2)))

    with pytest.warns(ValidationWarning, match="1 is a required value"):
        model.required_hdu = None
    assert_array_equal(model.required_hdu, np.zeros((2, 2)))


@pytest.mark.xfail(reason="validation of required attributes not yet implemented", strict=True)
def test_validation_on_delete():
    model = RequiredModel()

    with pytest.warns(None) as warnings:
        model.meta.required_keyword = "foo"
    assert len(warnings) == 0

    with pytest.warns(ValidationWarning):
        del model.meta.required_keyword
    assert model.meta.required_keyword == "foo"

    model = RequiredModel(pass_invalid_values=True)

    with pytest.warns(None) as warnings:
        model.meta.required_keyword = "foo"
    assert len(warnings) == 0

    with pytest.warns(ValidationWarning):
        del model.meta.required_keyword
    assert model.meta.required_keyword is None


def test_pass_invalid_values_attribute_assignment(monkeypatch):
    def assert_passed(model, passed):
        with pytest.warns(ValidationWarning):
            model.meta.string_attribute = 42
        if passed:
            assert model.meta.string_attribute == 42
        else:
            assert model.meta.string_attribute is None

    assert_passed(ValidationModel(), False)
    assert_passed(ValidationModel(pass_invalid_values=True), True)
    assert_passed(ValidationModel(pass_invalid_values=False), False)

    monkeypatch.setenv("PASS_INVALID_VALUES", "true")
    assert_passed(ValidationModel(), True)

    monkeypatch.setenv("PASS_INVALID_VALUES", "false")
    assert_passed(ValidationModel(), False)


@pytest.mark.xfail(reason="validation on write not yet implemented for ASDF files", strict=True)
def test_pass_invalid_values_on_write(tmp_path):
    file_path = tmp_path/"test.asdf"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    with pytest.warns(ValidationWarning):
        model.save(file_path)

    with asdf.open(file_path) as af:
        assert af["meta"]["string_attribute"] == 42


def test_strict_validation_attribute_assignment(monkeypatch):
    def assert_strict(model, strict):
        if strict:
            with pytest.raises(ValidationError):
                model.meta.string_attribute = 42
            assert model.meta.string_attribute is None
        else:
            with pytest.warns(ValidationWarning):
                model.meta.string_attribute = 42
            assert model.meta.string_attribute is None

    assert_strict(ValidationModel(), False)
    assert_strict(ValidationModel(strict_validation=True), True)
    assert_strict(ValidationModel(strict_validation=False), False)

    monkeypatch.setenv("STRICT_VALIDATION", "true")
    assert_strict(ValidationModel(), True)

    monkeypatch.setenv("STRICT_VALIDATION", "false")
    assert_strict(ValidationModel(), False)


def test_validate():
    model = ValidationModel(pass_invalid_values=True)

    with pytest.warns(None) as warnings:
        model.meta.string_attribute = "foo"
        model.validate()

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    assert model.meta.string_attribute == 42

    with pytest.warns(ValidationWarning):
        model.validate()


def test_validate_required_fields():
    model = FitsRequiredModel()

    with pytest.warns(ValidationWarning):
        model.validate_required_fields()

    model.meta.required_keyword = "foo"
    model.required_hdu = np.zeros((0, 0))
    with pytest.warns(None) as warnings:
        model.validate_required_fields()
    assert len(warnings) == 0


@pytest.mark.xfail(reason="validation on read not yet implemented for ASDF files", strict=True)
def test_validation_on_read(tmp_path):
    file_path = tmp_path/"test.asdf"
    with asdf.AsdfFile() as af:
        af["meta"] = {"string_attribute": "foo"}

        with pytest.warns(None) as warnings:
            ValidationModel(af)
        assert len(warnings) == 0

        af["meta"]["string_attribute"] = 42
        with pytest.warns(ValidationWarning):
            ValidationModel(af)


@pytest.mark.xfail(reason="validation on write not yet implemented for ASDF files", strict=True)
def test_validation_on_write(tmp_path):
    file_path = tmp_path/"test.asdf"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42

    with pytest.warns(ValidationWarning):
        model.save(file_path)
