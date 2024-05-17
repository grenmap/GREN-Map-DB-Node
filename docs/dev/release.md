# Creating and Publishing a Release

## Update the Codebase with Release Information

From a local workspace:

### 1. Pull 'main'

    git pull origin main
    git checkout -b "version-X.Y.Z"

### 2. Update Version

Increment the version number appropriately in /package.json

### 3. Update the Changelog

Make a section for the version to be released with the contents of the current unreleased section.

Create a new unreleased section above the section to be released.

Example:

Before the update:

```
## Unreleased

### Added

#5 Node health information
#4 Pause polling scheduler
```

After:

```
## Unreleased

## 1.0.1 2024-01-01

### Added

#5 Node health information
#4 Pause polling scheduler
```

### 4. Push to GitHub

    git commit -m "Version increment to X.Y.Z"
    git push --set-upstream origin version-X.Y.Z

## Create a GitHub Release

From GitHub:

### 5. Merge to 'main'

Create a pull request and perform the merge to 'main'.  Once that merge to 'main' has been completed, delete branch 'version-X.Y.Z'.

### 6. Make a Release

Follow GitHub procedures to create a Release. Create a tag and the release description observing conventions from previous releases. The release will trigger the "build image" action. It will push multi-architecture docker images to the GitHub container repository.
