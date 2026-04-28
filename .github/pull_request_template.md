<!-- If this PR closes a JIRA ticket, make sure the title starts with the JIRA issue number, 
for example JP-1234: <Fix a bug> -->
Resolves [JP-nnnn](https://jira.stsci.edu/browse/JP-nnnn)

<!-- If this PR closes a GitHub issue, reference it here by its number -->
Closes #

<!-- describe the changes comprising this PR here -->
This PR addresses ...

<!-- if you can't perform these tasks due to permissions, please ask a maintainer to do them -->
## Tasks
- [ ] update or add relevant tests
- [ ] update relevant docstrings and / or `docs/` page
- [ ] If this change affects user-facing code or public API, add news fragment file(s) to `changes/` (see [the changelog instructions](https://github.com/spacetelescope/stdatamodels/blob/main/changes/README.md)).
      Otherwise, add the `no-changelog-entry-needed` label.
- [ ] [run `jwst` regression tests](https://github.com/spacetelescope/RegressionTests/actions/workflows/jwst.yml) with this branch installed (`"git+https://github.com/<fork>/stdatamodels@<branch>"`)
