# GREN Map Database Node Documentation

The Global Research and Education Network (GREN) is a "network of networks" that links great minds to each other, and to technologies, research facilities, and data, enabling global research collaborations and education support.

The GREN Map is a database of this connectivity, to be used for visualizing it in both static and interactive displays.  It consists of a hierarchical distributed database: each Research and Education Network (REN) will maintain a database node of their own, and also aggregate the data from nodes for the smaller networks that it connects, on a regular polling interval. Ultimately, data will percolate up to a central node for the entire globe.

The individual databases that connect into this hierarchy are known as "nodes" (sometimes "DB nodes" where "node" might be an ambiguous term).  DB nodes can be configured to poll other DB nodes to pull remote data and consolidate it into its own database.

Documentation for the GREN Map DB Node consists of Markdown files, organized in a directory structure with three sections:

## Administrator Guide

`/docs/admin/`

This section is intended for operations personnel responsible for deploying, configuring, and maintaining an instance of the software.

Generally, deployment follows this pattern:
1. [Single Sign-On](admin/sso.md) is configured for a production instance.  For local evaluation or development, the SSO configuration in the [README](../README.md) Quick Start Guide is sufficient.
1. [Deployment](admin/deployment.md) of the node is performed.
1. [Configuration](admin/configuration.md) of the real-time settings in the administration section of the site may be tweaked.

## User Guide

`/docs/user/`

This section is intended for Data Administrators who will be using the software on a day-to-day basis.

Some basic day-to-day management of the Node will involve:
- [Admin Users](user/admin-users.md) management

If the Node is set up in a hierarchical distributed database, it will be either polling other Nodes for their data, or be polled for its own data, or both.
- [Polling: Adding Data Sources](user/polling.md) sets up remote sources of data.
- [Collation Rules](user/collation.md) are used when data gathered from other sources requires merging and fine-tuning.
- [Access Tokens](user/tokens.md) are a security and integrity measure required to allow other DB Nodes to poll this one for its data.  Tokens may also be required for certain API access.

Map data can be managed through the Django Admin, accessed via the /admin/ URL.  (A user must be logged in to access that URL.)  For more efficient bulk data entry, the DB Node accepts GRENML/XML files, and Excel spreadsheets following a particular template.
- [Importing Data Into the Node](user/grenml_import.md)
- [Public HTTP API](user/api.md)

## Developer Guide

`/docs/dev/`

This section is intended for software developers diagnosing issues and contributing to this source code repository.

### Contribution Guidelines

Before starting development on the DB Node, please review the following:
- [Contribution Guidelines](../CONTRIBUTING.md)
- [Development Guidelines](dev/development.md)
- [Dependency Management](dev/dependency_management.md)
- [Coding Conventions](dev/coding_conventions.md)
- [Documentation](dev/documentation.md)
- [Release Procedure](dev/release.md)
- [Changelog Update Procedure](dev/changelog.md)

### Common Topics

Some topics common to most development include:
- [Tests](dev/testing.md)
- [Logging](dev/logging.md)
- [Internationalization and Translation](dev/translation.md)

### Map Data Schema Overview

Network topologies and the objects they contain are represented by models in a Django ORM:
- [ORM Structure](dev/orm_grenml.md)

### Special Topics

More specific topics that may be helpful to developers working on particular areas:
- [Application Settings](dev/app_settings.md) are useful for allowing Administrators to configure the behaviour of the DB Node while the system is deployed and live.  New Application Settings may be added to increase this flexibility.
- [Collation Rules](dev/collation.md), including Match Types and Action Types, may be written to add more options for Data Administrators to refine data after merging sources.
- [Django Q Scheduling and Background Tasks](dev/django_q.md) is a topic generally useful for polling, large file handling, and other background tasks.
- [Importing and Polling](dev/import_polling.md) describes the mechanisms involved in the import and polling processes.
- [Security Headers](dev/security_headers.md) are set as suggestions for browser clients to treat the map site as secure.
- [Shared Storage with Redis](dev/shared_storage_redis.md) plays an important role as a buffer for incoming files while they are processed.
- [Writing API Endpoints](dev/writing_api_endpoints.md) is a helpful reference for adding HTTP-accessible functionality.
