# Dependency Management

To manage dependencies of external software, multiple package managers are used based on the language the dependency is for.

## Javascript browser dependencies

Any dependencies for the browser(such as the GREN map visualization) are in the package.json file in the django folder. To use dependencies from git follow the instructions at the following url:
    https://docs.npmjs.com/cli/v7/configuring-npm/package-json#git-urls-as-dependencies

## Python dependencies

Any Python dependencies used by Django should be defined in the requirements.txt file inside the django folder. To use dependencies from git follow the instructions at the following url:
    https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support
