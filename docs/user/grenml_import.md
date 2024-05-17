# Importing Data Into a Node

Initially the DB Node's map information database is empty. The import feature lets a user populate the map with network nodes and links.

The system can ingest GRENML and Excel files. GRENML is an XML-based format. A Python package for parsing GRENML files is available at [pypi.org](https://pypi.org/project/grenml). An example Excel file can be obtained from the [GRENML](https://github.com/grenmap/GRENML/blob/main/docs/Sample%20Conversion%20Spreadsheet/GREN_data.v1_0.xlsx) repository.

## Import an Excel or XML file Through Admin UI

Navigate to the admin page, using the `Home` link on the app's landing page or the url path `/admin`.

Click on `GRENML File Imports`, under the section Network Topology Import.  This page lists all files previously imported.

Click on the `Add GRENML File Import` button in the top right corner of the page.
- Use the `Browse` button to select a file.
- Choose a `Topology` from the `Parent Topology` dropdown.

_Every Topology must have an Institution set as its "owner" for import and export operations to function correctly._

It is mandatory to provide a `Topology name` for Excel file imports, as it cannot be inferred from the spreadsheet.  This must be left blank for GRENML/XML imports.

If the Topology name, whether read from the GRENML file or provided alongside the Excel file, matches an existing Topology name, that existing Topology will be updated with the new data in the file.  Otherwise, a new Topology will be created.

Proceed by clicking on any of the buttons `Save and add another`, `Save and view` or `DONE`. The app then returns to the imported files list page. It should display the file just imported.

Each entry in the `GRENML File Imports` page shows the name of a file imported, and some information about the status of the import procedure.  A click on an entry leads to a page that shows more information about the result of the import process; in case of failure, the page will show errors found in the file.

Click on `View Map` in the top right corner of the page to view the map showing nodes and links.

## Import XML file Through API Endpoint

The grenml_import API endpoint is at "/grenml_import/upload/" which is authorized by access tokens.

### Create an Access Token

See [Tokens Documentation](tokens.md) for instructions about how to create an Import Token (not a Polling Token).

### Post file to the API

Use python Requests:
```
requests.post(
    url='http://localhost/grenml_import/upload/',
    headers={"Authorization": "Bearer 4hT6YjO6oYmsdB0o77gSNZCz111"},
    files={'file': open('test.xml', 'r')},
)
```

With CURL command:
```
curl -X POST http://localhost/grenml_import/upload/ -H "Authorization: Bearer 4hT6YjO6oYmsdB0o77gSNZCz111" -F file=@test.xml
```

### OpenAPI Spec Excerpt

```yaml
openapi: 3.0.3
info:
  title: GRENMap public API
  version: 0.1.0
  description: Global Map of Research and Education Networks
paths:
  /grenml_import/upload/:
    post:
      operationId: grenml_import_upload_create
      description: Use this endpoint to upload a GRENML file. <br> <br> Requires an
        "import" token. <br>Navigate to Home > Base App > Tokens in the admin site
        to obtain one.
      requestBody:
        content:
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/GRENMLImport'
        required: true
      security:
      - import token: []
      responses:
        '201':
          description: No response body
        '403':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessDenied'
          description: ''
components:
  schemas:
    AccessDenied:
      type: object
      description: |-
        Serializer for responses blocked due to missing
        or invalid token.
      properties:
        detail:
          type: string
      required:
      - detail
    GRENMLImport:
      type: object
      description: |-
        This informs the schema generator on which attributes should appear
        in the body of an import request.
      properties:
        file:
          type: string
          format: binary
        parent_topology_id:
          type: string
          description: ID of an existing topology.
        topology_name:
          type: string
          description: Name to be given to the file's root topology once the server
            imports it.
      required:
      - file
  securitySchemes:
    import token:
      type: http
      scheme: bearer
servers:
- url: ''
  description: GRENMap server
```

## Manual Data Import

It is also possible to add or update data in the database manually, especially after the initial bulk import has been performed.  See the [ORM model structure](../dev/orm_grenml.md) for an idea of how the types of objects are structured and fit together, notably:
- Topologies contain Institutions, Nodes, and Links (there is usually one Topology per Research and Education Network)
- Institutions are entities that "own" (own, manage, or participate in) Topologies, Nodes, and Links
- Nodes are dots on the map
- Links are lines on the map that connect two Nodes

It is recommended to add items in the order above.

- NOTE: Any future bulk imports to the same Topology (often done to update data) will first delete all data in the Topology, so manual updates done via the Django Admin will be lost.  If updates to bulk-imported data are required, it is recommended to choose a single strategy of either updating the spreadsheet or XML and re-importing, or performing the updates manually, not mix the two strategies.
