# Contributing to this project

Contributions to this project are always welcome.
As a contributor, here are the guidelines we would like you to follow:

 - [Code of Conduct](#code-of-conduct)
 - [Feature Requests](#feature-request)
 - [Issues and Bugs](#submitting-an-issue)
 - [Submission Guidelines](#submitting-a-pull-request-pr)
 - [Coding Rules](#coding-rules)
 - [Commit Message Guidelines](#commit-message-guidelines)

## Code of Conduct

Help keep this project open and inclusive. Please read and follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Feature Request

You can request a new feature by submitting an issue to our repository. If you would like to implement a new feature, please submit an issue with a proposal for your work first, to be sure that it can be used.
Please consider what kind of change it is:

* For a Major Feature, first open an issue and outline your proposal so that it can be discussed. This will also allow for better coordination of efforts, prevent duplication of work, and help you to craft the change so that it is successfully accepted into the project.
* Small Features can be crafted and directly submitted as a Pull Request.

## Submitting an Issue

Before you submit an issue, search the archive, maybe your question was already answered.

If your issue appears to be a bug, and hasn't been reported, open a new issue.
Help us to maximize the effort we can spend fixing issues and adding new
features by not reporting duplicate issues.  Providing the following information will increase the
chances of your issue being dealt with quickly:

* Overview of the Issue - if an error is being thrown a non-minified stack trace helps
* Motivation for or Use Case - explain what are you trying to do and why the current behavior is a bug for you
* Browsers and Operating System - is this a problem with all browsers?
* Reproduce the Error - provide an example of what causes the error to appear
* Screenshots - If relevant, include screenshots capturing the issue triage issues far more quickly than a text description.
* Related Issues - has a similar issue been reported before?
* Suggest a Fix - if you can't fix the bug yourself, perhaps you can point to what might be causing the problem (line of code or commit)

## Submitting a Pull Request (PR)

Before you submit your Pull Request (PR) consider the following guidelines:

* Search for an open or closed PR that relates to your submission. You don't want to duplicate effort.
* Fork the GREN-Map-DB-Node repository.
* Create your patch on the fork:
  * Follow our [Coding Conventions](docs/dev/coding_conventions.md).
  * Add the appropriate unit tests. All unit tests should pass in your development environment. The `check.sh` script runs the unit tests.
  * Add the appropriate functional tests. All functional tests should pass in your development environment. You can use the `functional_tests.sh` script to run them.
  * Run the linter and fix any problems it finds. The `check.sh` script invokes the linter.
  * Add an entry to the unreleased section of the [changelog](docs/dev/changelog.md).
  * Commit your changes using a descriptive commit message that follows our [commit message conventions](#commit-message-guidelines).
  * Push your branch to the remote:
      ```bash
      git push my-fork my-fix-branch
      ```
* In the remote, send a pull request to `master`.
* If we suggest changes then:
  * Make the required updates.
  * Update your fork, rebase your branch and force push to your remote repository (this will update your Pull Request):
    ```bash
    git rebase master -i
    git push -f
    ```
The maintainer will:

* Read the code changes and suggest any necessary updates.
* Pull the change, try it, run unit and functional tests, run the linter.
  * If the linter or any tests fail, the maintainer will not apply the PR.
  * If all is good, the maintainer applies the PR.

That's it! Thank you for your contribution!

### After your pull request is merged

After your pull request is merged, you can safely delete your fork and pull the updated main branch.

## Coding Rules

To ensure consistency throughout the source code, keep these rules in mind as you are working:

* All features or bug fixes must be tested by one or more specs (unit-tests).
* All public API methods must be documented.
* We follow the pep8 python style guide, but with some modifications. See [coding conventions](docs/dev/coding_conventions.md)

## Commit Message Guidelines

Commit messages should describe what commit changed and what task the commit affects. The message should always start with an ID of the issue being addressed from the issue management system being used.  Example:
```
git commit -m "#178 Removes obsolete functions from base_app's views file"
```
