# Collation Rules

Data in a GREN Map database node may come from many sources.  Data that is added and edited exclusively from in the web interface for the node may be further edited without concern, as can data that is imported a single time from another source, such as a spreadsheet.  However, when data arrives from other sources periodically, any local updates may be overwritten by the incoming data.  In addition, conflicting or duplicated database records may appear in a node when it receives information from peers through the polling mechanism.

Collation Rules are database changes that run after every database change, whether from a local change or following import of other sources such as spreadsheets, XML files, and especially peer node polling.  The administrator of a node may use these collation Rules to consolidate redundant information, make alterations that persist, and avoid data integrity problems.

## Simple Example

For example, consider a case of where a country-level network has set up polling to retrieve information from a province-level network to integrate both data sets, and this polling occurs daily.  The administrator for a country-level node wishes to add a label property to certain Links in the province's data, to make them consistent with their own labelling to be shown embedded on their website.  If these property labels are assigned directly in the UI, when the provincial network's database node is polled the next day, the labels would be discarded in favour of the freshest data from the import, which would still not contain those labels.

Instead, the administrator may configure a set of Rules, each of which would match a Link by its ID, and assign a label property to that Link.  This set of Rules would run after every database change, including the polling event.  Upon each poll, the data would be refreshed to reflect the incoming data, but the Rules would then apply the desired changes anew over top of that fresh data.

Even if the province in question were to alter some fields on those Links, those changes would propagate to the country level, and as long as the IDs remain the same, the desired labels would be added at that country level.

No upstream changes would occur in the province's data.

## Rule Structure

**Rules** exist as members of **Rulesets**.  Rulesets can be used to logically group related Rules, at the data administrator's discretion.

- NOTE: All enabled, well-formed Rulesets will run automatically after import of a spreadsheet or XML file, after polling other database nodes, and after adding or editing Nodes, Links, and Institutions through Admin UI.

Each Rule has **Match Criteria** and **Actions**.  Match Criteria define filters to select which GRENML elements in the database the Rule will affect.  Actions represent operations that modify records.  Match Criteria and Actions within a Rule must all operate on the same type of element (Institutions, Nodes, or Links), or the Rule will be considered misconfigured and will not run.

Some Match Criteria and Actions require additional information in order to function.  For example, a Match Criterion to match Links by ID would need to know what ID to match.  To accommodate this in a flexible way, each Match Criterion is associated to a list of key-value **Match Info** items.  The keys required for a given Match Criterion depends on the type of matching being done.  In our example here, matching Links by ID requires a key of "ID" and a value of the ID it's meant to select.  Some types of matching may require many Match Infos, and some none at all.  Actions have similar key-value **Action Info** items.  See the documentation for each type of Match and each type of Action in the UI to see a list of required and optional keys.

The following is the structure for a fictional example Rule link the one described in the last paragraph:

    Ruleset: "Remove Extra Links From Partner NRENs"

        Rule: "Delete TransAtlantic Link 47"

            Match Criterion: Match Link By ID

                MatchInfo: {key: "ID", value: "TransAtlantic47"}

            Action: Delete Link

                ActionInfo: <N/A>

## How A Rule Is Applied

Every Rule can be thought of as a pipeline, containing one or more Match Criteria and one or more Actions, in that order.  The pipeline starts with a collection of all the GRENML entity elements of a particular type (Nodes, Links, and Institutions) in the database; which type of element depends on which Match types and Action types have been configured in the Rule.

The first Match Criterion, if present, reduces that list to a subset of elements, according to some filter mechanism appropriate to each type of match and the input provided, and passes on that subset.

The next Match Criterion takes that subset and further reduces it to a smaller (or equal) subset, and so on.

After all Match Criteria have filtered the data in sequence, all Actions are performed, one at a time, for each element in the filtered subset.

### Examples

The following (fictional) examples illustrate how Rules might be structured.

#### Rule: "Merge 'CORE-OTT-3' with 'Ottawa 3 Core Router'"

    (Node Ottawa 3 Core Router, Node CORE-OTT-3, <many other Nodes>, <many Links>, <many Institutions>)

        Match Criterion: Match Node By ID {'id': 'CORE-OTT-3'}

    (Node CORE-OTT-3)  # only one element selected

        Action: Merge Into Node {'id': 'Ottawa 3 Core Router'}

    (Node Ottawa 3 Core Router)

Result: Node Ottawa 3 Core Router now has some additional Properties and fields from CORE-OTT-3, without overwriting anything in Ottawa 3 Core Router; all Links pointing to CORE-OTT-3 as endpoints now have Ottawa 3 Core Router as those endpoints; CORE-OTT-3 is removed from the database.

#### Rule: "Tag all Nodes with names greater than 'B' with an 'R' in their name with the tag 'Senior Node'"

(The Matches in this Rule do not exist; this is a hypothetical example to show future possibilities once more Match Types and Action Types are available.)

    (Node A, Node B, Node CN, Node CR, Link 1, Link 2, Link 3, Institution X, Institution Y)  # All elements in the DB

        Match Criterion: Match Node By Name Rank {'compare operation': '>', 'reference': 'B'}

    (Node CN, Node CR)

        Match Criterion: Match By Partial Name {'substring': 'B'}

    (Node CR)

        Action: Add Tag {'tag': 'Senior Node'}

    (Node CR)

        Action: Add Tag {'tag': 'Changed'}

    (Node CR)

Result: Node CR now has the tag 'Senior Node' and 'Changed'.

## Directions

### Create a New Rule Within a New Ruleset

1. On the main admin page, click on "Rulesets", in the "Collation" section.

2. Click on the right side button "Add Ruleset".

3. Enter the name for the new Ruleset on the topmost text field, then click on "Add another Rule". Enter the name for the new Rule.

4. Click on the "Save and continue editing" button on the right-bottom corner to reveal the remaining fields in the new Rule. One match criterion block and one action block should appear.

5. Do the steps for creating a Rule in an existing Ruleset, starting with step 2.5.

### 2. Create a New Rule in an Existing Ruleset

1. Click on "Rules" under the "Collation" section in the home admin page.

2. Click on the "Add Rule" button located at the top-right corner.

3. Select the Ruleset to which the new Rule will belong using the drop-down control at the top of the page.

4. Then enter a name for the new Rule.

5. Select a match type for the Rule's first match criterion. Add one or more match info items using the "Add another Match Info" button.
Hint: applying the "Save and continue editing" button after selecting a Match Type for Match Criteria will provide some additional help by identifying which Match Info keys are required.

6. Select an action type for the Rule's first action. You may add more actions by clicking on the "Add another Action" button.
The Actions must all apply to the same type of elements as the Match Criteria.  For example, Match Link By ID applies to Links; the Delete Node Action Type cannot be used in conjunction.
Hint: applying the "Save and continue editing" button after selecting an Action Type for Actions will provide some additional help by identifying which Action Info keys are required.

7. Click on "Done" at the bottom-right corner to save the Rule.

### Notes

Incomplete Rules, and Rules with syntax or usage errors will not run, but will not prevent other Rules from running.

Rules and Rulesets may be disabled, via each one's 'enabled' field.  Disabled Rules/sets will not run when all Rules are normally run.

The order of execution for Rulesets is determined by the 'priority' field, in ascending order.  The Rules within each Ruleset are also run in order of the 'priority' field, in ascending order.  Rules/sets with the same priority are run in arbitrary order.

## Rule Import & Export

Rules may be exported and imported.  This serves several useful purposes, including backup, and sharing painstakingly created Rules with peers.

### Exporting Rulesets

1. Open the Rulesets page: click on "Rulesets" in the "Collation" section of the home admin page.

2. Select one or more Rulesets by clicking on the checkboxes at the leftmost column in the Rulesets table.

3. Open the "Action" drop-down. Select "Export Ruleset(s) to file". Click on the "Go" button. Your browser will open a save-file dialog, to determine the location where the file containing the selected Rulesets will be saved. Complete the dialog.

### Importing Rulesets

We can use the import function to re-create a Ruleset previously exported to a file.

1. Open the Rulesets page; select "Rulesets" under "Collation" in the main admin page.

2. Click on the "import Rulesets" button at the top-right corner of the page.

3. Use the file picker dialog to choose a file containing Rulesets. Confirm the selection.

4. The Rulesets page should reload and show the Rulesets contained in the file. In case the import operation fails, the page will show an error message.

- NOTE: importing a file overwrites Rulesets in the database. Suppose the Ruleset below exists in the database.

    {
        "name": "simple_ruleset",
        "rule_set": [
            {
                "name": "delete_first_node",
                "actions": [
                    {
                        "action_type": "Delete Node",
                        "actioninfo_set": []
                    }
                ],
                "matchcriteria": [
                    {
                        "match_type": "Match Node by ID",
                        "matchinfo_set": [{"key": "ID", "value": "1"}]
                    }
                ]
            }
        ]
    }

If we import a file containing the Ruleset that follows, with the same name but different contents, it will replace the one above.

    {
        "name": "simple_ruleset",
        "rule_set": [
            {
                "name": "delete_second_node",
                "actions": [
                    {
                        "action_type": "Delete Node",
                        "actioninfo_set": []
                    }
                ],
                "matchcriteria": [
                    {
                        "match_type": "Match Node by ID",
                        "matchinfo_set": [{"key": "ID", "value": "2"}]
                    }
                ]
            }
        ]
    }

## Running Rules

Rules and Rulesets may be enabled or disabled, and contain a priority indicator.

Running a Ruleset runs each of the (enabled) Rules it contains in ascending order of their priority fields.

Rules may be run individually, but are typically run in a batch containing all enabled Rulesets after any database change (via UI, file import, or neighbour polling).  Running all Rulesets means iterating through each enabled Ruleset (thus the Rules each contains, in order, per above) in ascending order of the Ruleset's priority field.

### To manually execute a Rule

1. Go to the Rules page by clicking on "Rules" under "Collation" in the main admin page.

2. Find the Rule you want to execute, and ensure it is ready to run according to the "Health Check" column.  If this indicates a problem, edit the Rule (there should be helpful hints therein).

3. Click on its "Apply Rule" button.

## ID Collisions

GRENML IDs are meant to be unique.  Duplicates can cause problems.  Duplicate IDs could occur several ways, but the most common is when other database nodes contain information about the same infrastructure, and the data is then combined through the hierarchical polling mechanism of the distributed database that comprises the global GREN Map.

ID conflicts should be resolved quickly, and never persist.

### Example Cases

As a simple example, two countries on either side of the Atlantic ocean are connected by a transatlantic link.  Each country would likely represent this link in their own data.  (Ideally, they would use the same IDs to describe this infrastructure.  We will assume this to be the case for this example.)  When this data is pushed up to the global level GREN Map database node, that node will receive two versions of the data representing that link.  The administrator at the global level will need to resolve this conflict somehow, both so that there are not persistent duplicate IDs, but also so that there are not two copies of the same link shown on a map.

Another example is when IDs are not well-chosen, and one REN in one country names their nodes "Router 17", "Router 42", etc., and another country applies the same pattern.  Conflicts arising from this type of collision must be resolved too.

### Using Rules to Handle ID Collisions

The system allows duplicate IDs as a temporary situation, so that all data may be ingested, and then the Rules infrastructure may be leveraged to resolve any ID conflicts.  After all Rules are run, the goal is to eliminate all ID conflicts.

There are special Rulesets shipped with every instance of the GREN Map database node, with negative priority values to indicate that they should be run before all other Rules.  In most instances, the following order:

    1. Custom ID Collision Resolution (priority -1)
    2. Default ID Collision Resolution (priority 0)
    3. All Other Rulesets (priority >0)

Rules an administrator writes for resolving various individual ID collision cases belong in the "Custom ID Collision Resolution" Ruleset, or additional similar Rulesets with negative priorities.

Any ID collisions that remain after the custom ID collision Rules have run should be trapped by the "Default ID Collision Resolution" Ruleset, which will apply a basic catch-all set of Rules to ensure that ID collisions do not persist in the database and cause downstream problems.  These defaults may be edited by an administrator, but care should be taken to ensure that no ID collisions can persist.

Normal non-ID-collision-related Rulesets are run last, and are meant to always have positive priority values.

#### Example ID Collision Rules

Here are some examples of custom ID collision resolution Rules.  They should run before the defaults, either in the Custom ID Collision Resolution Ruleset with priority -1, or in another custom Ruleset with priority ≤1.

##### Use Higher Hierarchical Version

Picture a Topology scenario where Topology A has subtopologies B & C containing data polled from constituent RENs' DB Nodes.  Suppose B describes it main Topology owner Institution Braeson Networks, and A also describes Braeson Networks.  Often the default ID collision Rules will prioritize the version of Braeson B, since it is both refreshed on every poll, and that version might be assumed to be more "authoritative" given its provenance as main owner of Topology B.  However, for whatever reason, it is determined that the version of Braeson in A is in fact preferable.  We'd also like to flesh out the Properties and fields in the A version with those in B, wherever possible without obliterating the good data.  Capturing this in a custom Rule before the defaults can act on it is the solution.

    Ruleset: "Custom ID Collision Resolution"

        Rule: "Prefer Braeson from A"

            Match Criterion: Match Duplicate Institution

                MatchInfo: <N/A>

                # No need to do anything if there is no duplication

            Match Criterion: Match Institution By ID

                MatchInfo: {key: "ID", value: "BraesonNetworks"}

                # Narrow the scope to just Braeson Networks collisions

            Match Criterion: Match Institutions By Topology

                MatchInfo: {key: "Topology ID", value: "B"}

                # Select the version in B to be merged into the preferable version A

            Action: Merge Into Institution

                ActionInfo: {key: "ID", value: "BraesonNetworks"}, {key: "Topology ID", value: "A"}

                # Combine both Institutions by amalgamating all information from both elements, but preferring the information in A's copy
                # Update the version from A to own everything that the version from B owned
                # Deletes the version from B
