# Polling: Adding a remote source

Polling sources can be added by navigating to the admin page and using the "Polling" app. To add or manage polling sources, use the "GRENML Polling Sources" table and add a record with a descriptive name of the source, as well as selecting and filling out the relevant fields of the node you wish to poll.

The relevant fields for a polling node are as follows:
- **Name:** A label that you give the connection so that it's easy to identify where it's connection
- **Hostname:** The hostname to access the other organization's DB node
- **Active:** This identifies if the poller should contact this source or not
- **Path:** The path to the node. It should be formatted to end with a /
- **Token:** An access token provided by the source node's administrator. See the "Access Control Tokens" section below.

# Collecting Data from the Sources

All polled sources' Topologies will be added as children of the main Topology (see "Preparing to be polled" below), or as top-level root Topologies with no parents if there is no main Topology set.

## Polling All sources

All sources labeled active will have their data automatically collected by the scheduled polling mechanism at the interval specified in the "GRENML Polling Interval" setting in the App Configuration Settings table in the Admin, if "GRENML Polling Enabled" is set to "True".  See [Configuration](../admin/configuration.md) for more information on polling configuration.

All sources labeled active can be manually polled by navigating to the "Polling App" and clicking the button labeled "Collect All Active Sources' GRENML Data" at the bottom of the page.

A subset of sources can be polled by selecting the sources using the checkbox on the left side of the table, going to the dropdown at the top of the page, and selecting the option "Poll the Selected Sources" and clicking the button next to the dropdown.

- NOTE: This method will ignore the 'active' flag.

## Polling Single Sources

A single source can be polled at any time by navigating to the record in the "GRENML Polling Source" table and clicking the "Collect Data" button on the right of the table.

- NOTE: This will ignore the 'active' flag.

## Checking the Status of a Poll

Each poll of a source will produce a log in the form of a database object, available in the admin page for Source Poll Event Logs.  Available here is such information as the overall success of the poll operation (including the import of the data into the database), the source that was contacted, the time taken, and whether the poll was scheduled or triggered manually.

When polls are performed as part of a batch, including scheduled polls, these individual log entries are instead found under Batch Poll Event Logs.  The batch poll has similar information available as each individual source, and also lists the information for all sources polled.  Success of the batch is determined by the success of the individual sources; any single error or warning in the sources will cause the overall success to be downgraded accordingly.

# Checking Status of a Connection

## Checking Multiple Sources

Multiple sources can have their status checked at once by navigating to the "Polling App," select the sources to perform a status check, select "Check the Status of Selected Sources" from the dropdown at the top of the table, and click the "Go" button.

A message will appear at the top of the page listing the amount of successful connections, and list out the sources, by name, that failed to produce a successful connection.

Alternatively, there is a button labeled "Check All Sources' Connection Statuses" that can be clicked to perform a connection status check on all sources and report on all of them.

## Checking a Single Source

A single source can have its status checked by navigating to the record in the "GRENML Polling Source" table and clicking the "Test Connection" button

Alternatively, a source can be checked by navigating to the record and clicking the "Test Connection" button at the bottom of the page

# Access Control Tokens

GREN nodes use access tokens to decide if polling requests should be accepted or not.

Administrators can create tokens on their nodes and share them with administrators of peer nodes.

To register a peer node as a polling source, an administrator needs a token provided by the peer's administrator.

When a node sends a polling request to a peer, it attaches the peer's token to the message. The peer has a list of valid tokens. It will respond to the request if it finds the token attached in its list.

By deleting or modifying a token, an administrator can revoke access rights of peer nodes.

## How to Create an Access Token

From the main admin page, navigate to "Tokens", in the section "Base App".

Click on the "Add Token" button on the top right corner. Enter the client name which the token will be associated, and select the Token associated app with "Collecting Token For External Use" for polling purpose. Press "Save", on the bottom right corner.

The system then returns to the token list page, which now contains a new record showing the client name we provided, followed by a random string. The administrator of the peer node identified by that client name will need this string to register our node as a polling source.

# Preparing to be polled

## Main Root Topology

In order to serve as a polling source for another DB node higher in the hierarchy, a single Topology must be identified as the root for export.  That Topology and its tree of subtopologies will be exported to the polling node.

Topologies higher up in the local hierarchy, or unrelated to the selected main Topology, will be ignored during GRENML/XML export and polling.  However, they will still appear in map visualizations served directly by this DB node.

Important: Once a main Topology has been selected, it will also serve as the parent for all future polled sources' Topologies.

### Setting Main Root Topology

To select the root Topology for export, set the 'main' field on that Topology, either by editing the Topology, or using a Django Admin Action in the Topologies list page: select a single Topology, select the relevant action from the dropdown box at the top of the list, and press 'Go'.

Only one Topology may be set as 'main'.  Setting a Topology as main will automatically unset the previous main Topology's 'main' field.

## Publishing a Topology Snapshot

With a published version of the main Topology in place, it becomes a sort of snapshot of the map data, making it possible to change the map data and preview these changes locally without the changes propagating through the hierarchical distributed GREN Map database.

Published database snapshots are simply stored GRENML file exports.

### Making a Snapshot

From the `Published Database Snapshots` section, the `Add` button will open a form.  Give the snapshot a meaningful name (often a date stamp is useful here) and description, then the `Done` button will create the snapshot.

It is possible to list all snapshots from the same section.  This list will be shown after creation of a new snapshot if performed with the `Done` button.

### Configuration to Use the Snapshot

In the `App Configuration Settings` there is an item named `GRENML Polling Data Supply Type`.  It may be set to one of two values:
- "Live": the DB Node will serve live map data when polled, regardless of whether there is a published snapshot.
- "Published": the most recent snapshot will be selected and served when polled.

### Local Behaviour

The API for a DB Node with a published snapshot will always serve live data, regardless of the setting above.  This is so that local changes may be previewed.

# API

## Poll All Active Sources

There is an HTTP endpoint at `/polling/trigger/` to begin a poll of all active configured target source nodes.  This will, in arbitrary sequence, contact each configured target node, retrieve its published GRENML data, and import it into the local topology database with prejudice (overwriting any conflicting data).

There are other API endpoints, but they are strictly for testing and not meant to be used publicly.
