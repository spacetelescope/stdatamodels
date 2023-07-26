import numpy
import pytest

from stdatamodels.dynamicdq import dynamic_mask


def _dq(init):
    return numpy.array(init, dtype='u4')


def _dq_def(init):
    return numpy.array(init, dtype=[('VALUE', 'u4'), ('NAME', 'S40')])


class FakeModel:
    def __init__(self, dq, dq_def):
        self.dq = dq
        self.dq_def = dq_def


@pytest.mark.parametrize('dq', [[], [1, 2, 3]])
@pytest.mark.parametrize('dq_def', [None, 1, _dq_def([])])
@pytest.mark.parametrize('mmap', [{}, {'a': 1}])
@pytest.mark.parametrize('inv', [True, False])
def test_copy_dq(dq, dq_def, mmap, inv):
    dq = _dq(dq)
    model = FakeModel(dq, dq_def)
    dqmask = dynamic_mask(model, mmap, inv)
    assert dq is dqmask


@pytest.mark.parametrize('inv', [True, False])
def test_mmap(inv):
    dq = _dq([0, 1, 2, 4])
    dq_def = _dq_def([(1, 'FOO'), (2, 'BAR'), (4, 'BAM')])
    model = FakeModel(dq, dq_def)
    mmap = {
        b'FOO': 4,
        b'BAR': 1,
        b'BAM': 2,
    }
    dqmask = dynamic_mask(model, mmap, inv)
    if inv:
        numpy.testing.assert_equal(dqmask, [0, 2, 4, 1])
    else:
        numpy.testing.assert_equal(dqmask, [0, 4, 1, 2])


@pytest.mark.parametrize('inv', [True, False])
def test_missing_map_key(caplog, inv):
    dq = _dq([0, 1])
    dq_def = _dq_def([(1, 'FOO')])
    model = FakeModel(dq, dq_def)
    mmap = {
        b'BAR': 2,
    }
    dqmask = dynamic_mask(model, mmap, inv)
    numpy.testing.assert_equal(dqmask, [0, 0])
    assert 'does not correspond to an existing DQ' in caplog.text
