import asdf
import pytest
import numpy as np

from stdatamodels import DataModel

from models import BasicModel, AnyOfModel


def test_init_from_pathlib(tmp_path):
    """Test initializing model from a PurePath object"""

    file_path = tmp_path/"test.asdf"
    with asdf.AsdfFile() as af:
        af["meta"] = {"telescope": "crystal ball"}
        af.write_to(file_path)

    model = BasicModel(file_path)

    # Test is basically, did we open the model?
    assert model.meta.telescope == "crystal ball"


def test_set_shape():
    with BasicModel((50, 50)) as dm:
        assert dm.shape == (50, 50)

        with pytest.raises(AttributeError):
            dm.shape = (42, 23)


def test_broadcast():
    with BasicModel((50, 50)) as dm:
        data = np.empty((50,))
        dm.dq = data


def test_broadcast2():
    with BasicModel() as dm:
        data = np.empty((52, 50))
        dm.data = data

        dq = np.empty((50,))
        dm.dq = dq


def test_delete():
    with BasicModel() as dm:
        dm.meta.telescope= 'JWST'
        assert dm.meta.telescope == 'JWST'
        del dm.meta.telescope
        assert dm.meta.telescope is None


def test_copy():
    with BasicModel((50, 50)) as dm:
        dm.meta.telescope = "MEADE"
        dm.meta.foo = "BAR"

        with dm.copy() as dm2:
            dm2.data[0, 0] = 42
            assert np.sum(dm.data.flatten()) == 0

            assert dm2.meta.telescope == "MEADE"
            assert dm2.meta.foo == "BAR"
            dm2.meta.foo = "BAZ"
            assert dm.meta.foo == "BAR"
            dm2.meta.origin = "STScI"
            assert dm.meta.origin is None


def test_stringify(tmp_path):
    dm = DataModel()
    assert str(dm) == '<DataModel>'

    dm = BasicModel((10, 100))
    assert str(dm) == '<BasicModel(10, 100)>'

    file_path = tmp_path/"test.asdf"
    dm.save(file_path)
    dm.close()

    with BasicModel(file_path) as dm:
        assert str(dm) == '<BasicModel(10, 100) from test.asdf>'


def test_init_with_array():
    array = np.empty((50, 50))
    with BasicModel(array) as dm:
        assert dm.data.shape == (50, 50)


def test_init_with_array2():
    with pytest.raises(ValueError):
        array = np.empty((50,))
        with BasicModel(array) as dm:
            dm.data


def test_set_array():
    with pytest.raises(ValueError):
        with BasicModel() as dm:
            data = np.empty((50,))
            dm.data = data


def test_set_array2():
    with BasicModel() as dm:
        data = np.empty((50, 50))
        dm.data = data


def test_base_model_has_no_arrays():
    with pytest.raises(AttributeError):
        with DataModel() as dm:
            dm.data


def test_array_type():
    with BasicModel() as dm:
        assert dm.dq.dtype == np.uint32


def test_copy_model():
    with DataModel() as dm:
        with DataModel(dm) as dm2:
            assert hasattr(dm2, 'meta')


def test_dtype_match():
    with BasicModel() as dm:
        dm.data = np.array([[1, 2, 3]], np.float32)


def test_default_value_anyof_schema():
    """Make sure default values are set properly when anyOf in schema"""
    with AnyOfModel() as dm:
        assert dm.meta.foo is None


def test_secondary_shapes():
    """
    Confirm that a non-primary array takes on the shape
    specified in the initializer.
    """
    with BasicModel((256, 256)) as dm:
        assert dm.area.shape == (256, 256)


def test_initialize_arrays_with_arglist():
    shape = (10, 10)
    area = np.full((2, 2), 13.0)
    m = BasicModel(shape, area=area)
    assert np.array_equal(m.area, area)


def test_open_asdf_model(tmp_path):
    # Open an empty asdf file, pass extra arguments
    with DataModel(ignore_version_mismatch=False, ignore_unrecognized_tag=True) as model:
        assert not model._asdf._ignore_version_mismatch
        assert model._asdf._ignore_unrecognized_tag

    file_path = tmp_path/"test.asdf"

    with asdf.AsdfFile() as af:
        af.write_to(file_path)

    with DataModel(file_path, ignore_version_mismatch=False, ignore_unrecognized_tag=True) as model:
        assert not model._asdf._ignore_version_mismatch
        assert model._asdf._ignore_unrecognized_tag


def test_open_model_s3(s3_root_dir):
    path = str(s3_root_dir.join("test.asdf"))
    with DataModel() as dm:
        dm.save(path)

    model = DataModel("s3://test-s3-data/test.asdf")
    assert isinstance(model, DataModel)


def test_update_from_dict(tmp_path):
    """Test update method from a dictionary"""
    file_path = tmp_path/"update.asdf"
    with BasicModel((5, 5)) as m:
        m.update({"foo": "bar", "baz": 42})
        m.save(file_path)

    with asdf.open(file_path) as af:
        assert af["foo"] == "bar"
        assert af["baz"] == 42


def test_object_node_iterator():
    m = BasicModel({"meta": {"foo": "bar"}})
    items = []
    for i in m.meta.items():
        items.append(i[0])

    assert 'foo' in items


def test_hasattr():
    model = DataModel({"meta": {"foo": "bar"}})
    assert model.meta.hasattr('foo')
    assert not model.meta.hasattr('baz')


def test_datamodel_raises_filenotfound(tmp_path):
    file_path = tmp_path/"missing.asdf"

    with pytest.raises(FileNotFoundError):
        DataModel(file_path)


def test_getarray_noinit_valid():
    """Test for valid value return"""
    arr = np.ones((5, 5))
    model = BasicModel(data=arr)
    fetched = model.getarray_noinit('data')
    assert (fetched == arr).all()


def test_getarray_noinit_raises():
    """Test for error when accessing non-existent array"""
    arr = np.ones((5, 5))
    model = BasicModel(data=arr)
    with pytest.raises(AttributeError):
        model.getarray_noinit('area')


def test_getarray_noinit_noinit():
    """Test that calling on a non-existant array does not initialize that array"""
    arr = np.ones((5, 5))
    model = BasicModel(data=arr)
    try:
        model.getarray_noinit('area')
    except AttributeError:
        pass
    assert 'area' not in model.instance


@pytest.mark.parametrize("filename", ["null.fits", "null.asdf"])
def test_skip_serializing_null(tmp_path, filename):
    """Make sure that None is not written out to the ASDF tree"""
    file_path = tmp_path/filename
    with BasicModel() as model:
        model.meta.telescope = None
        model.save(file_path)

    with BasicModel(file_path) as model:
        # Make sure that 'telescope' is not in the tree
        with pytest.raises(KeyError):
            assert model.meta["telescope"] is None


def test_delete_failed_model():
    """
    Test that a model that failed to initialize does not
    error when deleted.
    """
    class FailedModel(DataModel):
        def __init__(self, *args, **kwargs):
            # Simulate a failed init by not invoking the
            # superclass __init__.
            pass

    model = FailedModel()
    # "Asserting" no error here:
    model.__del__()


def test_on_init_hook():
    class OnInitModel(DataModel):
        def on_init(self, init):
            super().on_init(init)

            self.meta.foo = "bar"

    model = OnInitModel()
    assert model.meta.foo == "bar"


def test_on_save_hook(tmp_path):
    class OnSaveModel(DataModel):
        def on_save(self, init):
            super().on_save(init)

            self.meta.foo = "bar"

    model = OnSaveModel()
    assert model.meta.get("foo") is None
    model.save(tmp_path/"test.asdf")
    assert model.meta.foo == "bar"
