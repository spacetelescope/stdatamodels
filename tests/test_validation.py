import pytest

import asdf
from jsonschema import ValidationError

from stdatamodels.validate import ValidationWarning

from models import ValidationModel, RequiredModel


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
    assert len(warnings) == 0

    with pytest.warns(ValidationWarning):
        model.meta.required_attribute = None


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


@pytest.mark.parametrize(
    "init_value,env_value,passed",
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


def test_pass_invalid_values_on_write(tmp_path):
    file_path = tmp_path/"test.asdf"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    with pytest.warns(ValidationWarning):
        model.save(file_path)

    with asdf.open(file_path) as af:
        assert af["meta"]["string_attribute"] == 42


@pytest.mark.parametrize(
    "init_value,env_value,exception_class",
    [
        (None, None, ValidationWarning),
        (True, None, ValidationError),
        (False, None, ValidationWarning),
        (None, "true", ValidationError),
        (None, "false", ValidationWarning),
    ],
)
def test_strict_validation_attribute_assignment(monkeypatch, init_value, env_value, exception_class):
    if env_value is not None:
        monkeypatch.setenv("STRICT_VALIDATION", env_value)

    model = ValidationModel(strict_validation=init_value)

    if issubclass(exception_class, Warning):
        with pytest.warns(exception_class):
            model.meta.string_attribute = 42
        assert model.meta.string_attribute is None
    else:
        with pytest.raises(exception_class):
            model.meta.string_attribute = 42
        assert model.meta.string_attribute is None


def test_validate():
    model = ValidationModel(pass_invalid_values=True)

    with pytest.warns(None) as warnings:
        model.meta.string_attribute = "foo"
        model.validate()
    assert len(warnings) == 0

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42
    assert model.meta.string_attribute == 42

    with pytest.warns(ValidationWarning):
        model.validate()


@pytest.mark.xfail(reason="validation on init not yet implemented for ASDF files", strict=True)
def test_validation_on_init(tmp_path):
    with asdf.AsdfFile() as af:
        af["meta"] = {"string_attribute": "foo"}

        with pytest.warns(None) as warnings:
            ValidationModel(af)
        assert len(warnings) == 0

        af["meta"]["string_attribute"] = 42
        with pytest.warns(ValidationWarning):
            ValidationModel(af)


def test_validation_on_write(tmp_path):
    file_path = tmp_path/"test.asdf"
    model = ValidationModel(pass_invalid_values=True)
    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42

    with pytest.warns(ValidationWarning):
        model.save(file_path)

def test_validate_on_assignment_default():
    model = ValidationModel()
    assert model._validate_on_assignment==True

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42  # Bad assignment
    assert model.meta.string_attribute is None


def test_validate_on_assignment_false(tmp_path):
    file_path = tmp_path/"test.asdf"

    model = ValidationModel(validate_on_assignment=False)
    assert model._validate_on_assignment==False

    model.meta.string_attribute = 42  # Bad assignment should cause no warning
    assert model.meta.string_attribute == 42

    with pytest.warns(ValidationWarning):
        model.save(file_path)


def test_validate_on_assignment_true():
    model = ValidationModel(validate_on_assignment=True)
    assert model._validate_on_assignment==True

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42  # Bad assignment
    assert model.meta.string_attribute is None


def test_validate_on_assignment_with_environ_false(monkeypatch, tmp_path):
    file_path = tmp_path/"test.asdf"

    monkeypatch.setenv("VALIDATE_ON_ASSIGNMENT", "False")
    model = ValidationModel()
    assert model._validate_on_assignment==False

    model.meta.string_attribute = 42  # Bad assignment should cause no warning
    assert model.meta.string_attribute == 42

    with pytest.warns(ValidationWarning):
        model.save(file_path)


def test_validate_on_assignment_with_environ_true(monkeypatch, tmp_path):
    monkeypatch.setenv("VALIDATE_ON_ASSIGNMENT", "True")
    model = ValidationModel()
    assert model._validate_on_assignment==True

    with pytest.warns(ValidationWarning):
        model.meta.string_attribute = 42  # Bad assignment
    assert model.meta.string_attribute is None


def test_validate_on_assignment_setitem_default():
    model = ValidationModel()

    model.meta.list_attribute.append({"string_attribute": "foo"})
    assert model.meta.list_attribute[0].string_attribute == "foo"

    model.meta.list_attribute[0] = {"string_attribute": "bar"}
    assert model.meta.list_attribute[0].string_attribute == "bar"

    model.meta.list_attribute[0].string_attribute = "foo"
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.list_attribute[0] = {"string_attribute": 42}
    assert model.meta.list_attribute[0].string_attribute == "foo"

    with pytest.warns(ValidationWarning):
        model.meta.list_attribute[0].string_attribute = 42
    assert model.meta.list_attribute[0].string_attribute == "foo"

def test_validate_on_assignment_setitem_false():
    model = ValidationModel(validate_on_assignment=False)

    model.meta.list_attribute.append({"string_attribute": "foo"})
    assert model.meta.list_attribute[0].string_attribute == "foo"

    model.meta.list_attribute[0] = {"string_attribute": 42}
    assert model.meta.list_attribute[0].string_attribute == 42

    model.meta.list_attribute[0].string_attribute = 13
    assert model.meta.list_attribute[0].string_attribute == 13


def test_validate_on_assignment_insert_default():
    model = ValidationModel()
    attr_list = [
        {"string_attribute": "foo"},
    ]
    for x in attr_list:
        model.meta.list_attribute.append(x)
    assert model.meta.list_attribute[0].string_attribute == "foo"

    model.meta.list_attribute.insert(0,{"string_attribute": "bar"})
    assert model.meta.list_attribute[0].string_attribute == "bar"

    with pytest.warns(ValidationWarning):
        model.meta.list_attribute.insert(0,{"string_attribute": 42})
    assert model.meta.list_attribute[0].string_attribute == "bar"


def test_validate_on_assignment_insert_false():
    model = ValidationModel(validate_on_assignment=False)
    attr_list = [
        {"string_attribute": "foo"},
    ]
    for x in attr_list:
        model.meta.list_attribute.append(x)
    assert model.meta.list_attribute[0].string_attribute == "foo"

    model.meta.list_attribute.insert(0,{"string_attribute": 42})
    assert model.meta.list_attribute[0].string_attribute == 42
