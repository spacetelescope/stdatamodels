# stdatamodels

[![CI](https://github.com/spacetelescope/stdatamodels/actions/workflows/ci.yml/badge.svg)](https://github.com/spacetelescope/stdatamodels/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/spacetelescope/stdatamodels/branch/main/graph/badge.svg?token=TrmUKaTP2t)](https://codecov.io/gh/spacetelescope/stdatamodels)


Provides `DataModel`, which is the base class for data models implemented in the JWST and Roman calibration software.


## Unit Tests

A few unit tests require downloading (~500MB) data from CRDS. CRDS must be configured for these tests to pass
(see the [CRDS User Guide](https://jwst-crds.stsci.edu/static/users_guide/index.html)
for more information). Minimally (if not on the stsci vpn where the default path of
`/grp/crds/cache` is available) you will need to set `CRDS_PATH`.

```bash
export CRDS_PATH=/tmp/crds_cache/jwst_ops
```

These tests can also be skipped with the `no-crds` pytest option

```bash
pytest --no-crds
```
