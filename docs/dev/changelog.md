
# Updating the Changelog

The changelog should be updated on the completion of every task as a whole. Individual commits should not be added as a change.  Generally, each story or related group of stories merits an entry in the changelog.  Sufficient explanation of what was changed with regards to the change category should be provided in concise language.

## Build Dependencies

The file [django/requirements.txt](https://github.com/grenmap/GREN-Map-DB-Node/blob/main/django/requirements.txt) in the [gren-map-db-node](https://github.com/grenmap/GREN-Map-DB-Node) repository specifies the versions for the [grenml](https://github.com/grenmap/GRENML) packages.

The file package.json specifies the [gren-map-visualization](https://github.com/grenmap/gren-map-visualization) version.

## Changelog Sections

A section in the changelog has three parts.

1. The header has a date and a release identifier.
2. The build dependencies table has two columns: first is dependency name, second is dependency version.
3. List of tasks resolved.

Sections are ordered by date of release, latest to earliest.

The release identifiers have three numeric components and should change in accordance with the [Semantic Versioning specification](https://semver.org).

There are two GREN packages that are build dependencies of GREN Map DB Node: Map Visualization and GRENML. A task's changelog entry should mention changes in the versions of any of these dependencies.

## Unreleased

There should be a "unreleased" section in the file for changes that are upcoming or not implemented in the current release.

## Date Format
Dates in the changelog should take the format of yyyy-mm-dd,
as it follows the general convention for changelog files. This format also doesn't overlap in
ambiguous ways with other date formats, unlike some regional formats that switch the position of
month and day numbers. These reasons, and the fact this date format is an ISO standard, are why
it is the recommended date format for changelog entries.

## Change Categories

### Added
Any features that have been added that did not exist in the previous version should be under
the 'Added' category.

### Changed
Changes to existing functionality should go under the 'Changed' category.

### Deprecated
Any features that are intended to be removed should go under this category, with a suggestion
of a replacement for the functionality or a reason for its removal.

### Removed
Any features that are removed from the software completely should go under this category.

### Fixed
Whenever a bug or issue is identified and resolved it should go under this category.

### Security
Any changes regarding security fixes should go under this category.

## Examples

- NOTE: the release identifiers and package versions below are not real.

## Unreleased

### Changed

```
#7 Reorders fields in the entity pages

# 0.1.1 2021-02-01

| Dependency        | Version |
|-------------------|---------|
| Map-Visualization | 0.1.1   |
| GRENML            | 0.1.1   |
```

### Changed

```
#6 Updates model list descriptions

# 0.1.0 2021-01-01

| Dependency        | Version |
|-------------------|---------|
| Map-Visualization | 0.1.1   |
| GRENML            | 0.1.0   |
```

### Added

```
#5 Node health information
#4 Pause polling scheduler
#3 Implement translation mechanism
#1 Arbitraty Element Attributes
adds GRENML 0.1.0, Map-Visualization 0.1.0
```

### Fixed

```
#2 BUG: Cannot reset invalid value on GRENML Polling interval
```
