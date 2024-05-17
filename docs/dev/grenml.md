# GRENML: Map Data Export and Import

The primary bulk data format used for population of each map node's database, and communication between nodes in the distributed hierarchy, is "GRENML", an XML format loosely based on NML (Network Markup Language).

## Parsing and Writing

The Python library 'grenml', co-developed with this database node application, is leveraged to write and parse this format internally.

This library may also be used by third-party applications to produce input files to populate the database, either once or in an ongoing fashion.

When Excel spreadsheet files are imported, they are first converted to GRENML using the library.

This library contains more extensive documentation about using it, and the format itself.

## Topology Internal Completeness and Self-Consistency

The root element in any GRENML document is a Topology object, and further Topologies may be nested therein.  All map data (Institutions, Nodes, and Links) must be contained in a Topology.

Each Topology must be "complete", a restriction not required by the database schema.  This applies to ownership relationships: Topologies, Nodes, and Links are "owned" by Institutions; and Link endpoint relationships: Links must have two Nodes describing its endpoints.  In the database, these relationships may cross Topology boundaries, whether these Topologies are "related" (parent/child), or not (two independent Topology trees).

An exported  GRENML document may not always include all the Topologies in the database.  And regardless of this, import is simpler if each Topology can be fully self-contained.  For example, a Link may have one of its endpoint Nodes in another Topology, and this other Topology may happen to be imported after the Link's; this would be difficult to handle.  Thus, there is a requirement for "completeness" of each Topology.  The troublesome Node in the example above should be repeated in the Link's Topology.

Continuing to use the example above, it would also be problematic to have two copies of the Node in the database after the Link's Topology has been imported, with its copy of the Node, and the Node's original Topology has been imported too.

In such cases, where an element has been repeated for the purpose of completeness, a special Property is added to the element during export, with a special name:

    !-from-topology

The value of this special Property indicates the GRENML ID of the Topology/-ies from which it originated.  This special Property is recognized during import.  After import of each Topology, an attempt is made to locate the original copy of any elements with such a Property, and if it is found, the non-original copy of the element is deleted, and any relationships to it (ownership or endpoints) are redirected back to the original.  If the original is not found, a copy may persist indefinitely, but will continue to be marked with this special Property in hopes of eventually relinking the relationships correctly.
