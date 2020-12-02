0.1.0 (unreleased)
==================

- Create package and import code from jwst.datamodels. [#1]

- Remove stdatamodels.open. [#2]

- Fix validation behavior when an object with nested None values is
  assigned to a DataModel attribute. [#45]

- Rename is_builtin_fits_keyword to make clear that it is
  used outside of this package. [#47]
