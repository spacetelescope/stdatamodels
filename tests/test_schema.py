import pytest
import numpy as np
from numpy.testing import assert_array_equal

import asdf
from asdf.tags.core import NDArrayType
import jsonschema
from astropy.modeling import models

from stdatamodels.schema import merge_property_trees, build_docstring
from stdatamodels import DataModel

from models import FitsModel, TransformModel, BasicModel, ValidationModel, TableModel


@pytest.mark.parametrize("filename", ["test.asdf", "test.fits"])
def test_ad_hoc_attributes(filename, tmp_path):
    """
    Test that attributes unrecognized by the schema
    can still be assigned and written.
    """
    file_path = tmp_path/filename
    with DataModel() as dm:
        dm.meta.foo = {'a': 42, 'b': ['a', 'b', 'c']}

        dm.save(file_path)

    with DataModel(file_path) as dm2:
        assert dm2.meta.foo == {'a': 42, 'b': ['a', 'b', 'c']}


def test_find_fits_keyword():
    with FitsModel() as x:
        assert x.find_fits_keyword('TELESCOP') == ['meta.telescope']


def test_search_schema():
    with BasicModel() as x:
        results = x.search_schema('origin')

    assert [x[0] for x in results] == ['meta.origin']


def test_dictionary_like():
    with ValidationModel(strict_validation=True) as x:
        x.meta.string_attribute = 'FOO'
        assert x['meta.string_attribute'] == 'FOO'

        with pytest.raises(jsonschema.ValidationError):
            x['meta.string_attribute'] = 12

        with pytest.raises(KeyError):
            x['meta.FOO.BAR.BAZ']


def test_to_flat_dict():
    array = np.arange(1024)

    with DataModel() as x:
        x.meta.origin = 'FOO'
        x.data = array
        assert x['meta.origin'] == 'FOO'

        d = x.to_flat_dict()

        assert d['meta.origin'] == 'FOO'
        assert_array_equal(d['data'], array)

        d = x.to_flat_dict(include_arrays=False)
        assert "data" not in d


def test_to_flat_dict_ndarraytype(tmp_path):
    file_path = tmp_path / "test.asdf"

    array = np.arange(1024)
    with asdf.AsdfFile() as af:
        af["data"] = array
        af.write_to(file_path)

    with DataModel(file_path) as dm:
        d = dm.to_flat_dict()
        assert_array_equal(d["data"], array)
        assert isinstance(d["data"], NDArrayType)

        d = dm.to_flat_dict(include_arrays=False)
        assert "data" not in d


@pytest.mark.parametrize("filename", ["test.asdf", "test.fits"])
def test_table_array_shape_ndim(filename, tmp_path):
    file_path = tmp_path/filename
    with TableModel() as x:
        x.table = [
            (
                -42,
                42000,
                37.5,
                'STRING',
                [[37.5, 38.0], [39.0, 40.0], [41.0, 42.0]],
                [[37.5, 38.0], [39.0, 40.0], [41.0, 42.0]],
            )
        ]
        assert x.table.dtype == [
            ('int16_column', '=i2'),
            ('uint16_column', '=u2'),
            ('float32_column', '=f4'),
            ('ascii_column', 'S64'),
            ('float32_column_with_shape', '=f4', (3, 2)),
            ('float32_column_with_ndim', '=f4', (3, 2)),
        ]

        x.save(file_path)

    with TableModel(file_path) as x:
        assert np.can_cast(
            x.table.dtype,
            [
                ('int16_column', '=i2'),
                ('uint16_column', '=u2'),
                ('float32_column', '=f4'),
                ('ascii_column', 'S64'),
                ('float32_column_with_shape', '=f4', (3, 2)),
                ('float32_column_with_ndim', '=f4', (3, 2)),
            ],
            'equiv',
        )

    with TableModel() as x:
        with pytest.raises(ValueError):
            x.table = [
                (
                    -42,
                    42000,
                    37.5,
                    'STRING',
                    # This element should fail because it's shape is (2, 2) and not (3, 2):
                    [[37.5, 38.0], [39.0, 40.0]],
                    [[37.5, 38.0], [39.0, 40.0], [41.0, 42.0]],
                )
            ]


def test_implicit_creation_lower_dimensionality():
    with BasicModel(np.zeros((10, 20))) as m:
        assert m.dq.shape == (20,)


def test_add_schema_entry():
    with DataModel(strict_validation=True) as dm:
        dm.add_schema_entry('meta.foo.bar', {'enum': ['foo', 'bar', 'baz']})
        dm.meta.foo.bar
        dm.meta.foo.bar = 'bar'
        try:
            dm.meta.foo.bar = 'what?'
        except jsonschema.ValidationError:
            pass
        else:
            assert False


def test_validate_transform(tmp_path):
    """
    Tests that custom types, like transform, can be validated.
    """
    file_path = tmp_path/"test.asdf"
    with TransformModel(transform=models.Shift(1) & models.Shift(2), strict_validation=True) as m:
        m.validate()
        m.save(file_path)

    with TransformModel(file_path, strict_validation=True) as m:
        m.validate()


@pytest.mark.parametrize('combiner', ['anyOf', 'oneOf'])
def test_merge_property_trees(combiner):

    s = {
         'type': 'object',
         'properties': {
             'foobar': {
                 combiner: [
                     {
                         'type': 'array',
                         'items': [ {'type': 'string'}, {'type': 'number'} ],
                         'minItems': 2,
                         'maxItems': 2,
                     },
                     {
                         'type': 'array',
                         'items': [
                             {'type': 'number'},
                             {'type': 'string'},
                             {'type': 'number'}
                         ],
                         'minItems': 3,
                         'maxItems': 3,
                     }
                 ]
             }
         }
    }

    # Make sure that merge_property_trees does not destructively modify schemas
    f = merge_property_trees(s)
    assert f == s


def test_schema_docstring():
    template = "{fits_hdu} {title}"
    docstring = build_docstring(FitsModel, template).split("\n")
    for i, hdu in enumerate(('SCI', 'DQ', 'ERR')):
        assert docstring[i].startswith(hdu)
