# Public HTTP API

The following HTTP API endpoints are considered public and available for use.

This document contains an overview, and an example OpenAPI spec; for more details, an up-to-date OpenAPI spec may be generated with the following command:
```
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python manage.py spectacular --generator-class base_app.schema.GRENMapSchemaGenerator
```

## status/

Returns a simple set of details indicating the health status of the GREN Map DB Node instance.

## grenml_import/upload/

Accepts a GRENML file and ingests its contents into the database.  This may overwrite existing data; all Rules will be run.

POST to this endpoint using Python Requests:
```
requests.post(
    url='http://localhost/grenml_import/upload/',
    headers={"Authorization": "Bearer 4hT6YjO6oYmsdB0o77gSNZCz111"},
    files={'file': open('test.xml', 'r')},
)
```

POST to this endpoint using a CURL command:
```
curl -X POST http://localhost/grenml_import/upload/ -H "Authorization: Bearer 4hT6YjO6oYmsdB0o77gSNZCz111" -F file=@test.xml
```

In both examples above, a sample Token is shown as `4hT6YjO6oYmsdB0o77gSNZCz111`.  Configuration of a [Token](../user/tokens.md) prior to use of these APIs is required.

## grenml_export/

Fetches a GRENML file representing the root Topology in the database, including all its subtopologies.  This file may be generated live, or based on a pre-published snapshot, as configured in the node.

## published_network_data/current/grenml_export/

Fetches a GRENML file, similar to above, but only the latest snapshot (if available).

## Full OpenAPI Spec

```yaml
openapi: 3.0.3
info:
  title: GRENMap public API
  version: 0.1.0
  description: Global Map of Research and Education Networks
paths:
  /grenml_export/:
    get:
      operationId: grenml_export_retrieve
      description: Depending on the server's "Polling Data Supply Type" configuration
        parameter, <br> returns the root topology in the database as a GRENML file,
        or the latest snapshot file created. <br> <br> All nodes, links and institutions
        under the root topology and its child topologies <br> are saved in the file
        when the server creates it. <br> <br> To see or modify the supply type parameter,
        go to the admin site and <br> navigate to Home > Base App > App Configuration
        Settings. <br> <br> To create a snapshot, open the admin site and navigate
        to Home > Published Network Data. <br> <br>Requires a "polling" token. <br>Navigate
        to Home > Base App > Tokens in the admin site to obtain one.
      security:
      - polling token: []
      responses:
        '200':
          content:
            '*/*':
              schema:
                $ref: '#/components/schemas/GRENMLExport'
          description: ''
        '403':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessDenied'
          description: ''
        '500':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: ''
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
  /published_network_data/current/grenml_export/:
    get:
      operationId: published_network_data_current_grenml_export_retrieve
      description: Returns the snapshot of the server's data, as a GRENML file. <br>
        <br> To create a snapshot, open the admin site and navigate to Home > Published
        Network Data. <br> <br>Requires a "polling" token. <br>Navigate to Home >
        Base App > Tokens in the admin site to obtain one.
      security:
      - polling token: []
      responses:
        '200':
          content:
            '*/*':
              schema:
                $ref: '#/components/schemas/GRENMLExport'
          description: ''
        '403':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessDenied'
          description: ''
  /status/:
    get:
      operationId: status_retrieve
      description: Health check endpoint.
      responses:
        '200':
          description: No response body
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
    Error:
      type: object
      description: |-
        This declares a response containing an error,
        currently used by the exporting endpoint.
      properties:
        error_type:
          $ref: '#/components/schemas/ErrorTypeEnum'
      required:
      - error_type
    ErrorTypeEnum:
      enum:
      - MissingRootTopologyException
      - MissingRootTopologyOwnerException
      - NoTopologyOwnerError
      - Exception
      type: string
      description: |-
        * `MissingRootTopologyException` - MissingRootTopologyException
        * `MissingRootTopologyOwnerException` - MissingRootTopologyOwnerException
        * `NoTopologyOwnerError` - NoTopologyOwnerError
        * `Exception` - Exception
    GRENMLExport:
      type: object
      description: |-
        This represents the response body of export calls
        (those returning the server's network information stored in
        the database or in a snapshot file).
      properties:
        file:
          type: string
          format: uri
      required:
      - file
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
    polling token:
      type: http
      scheme: bearer
servers:
- url: ''
  description: GRENMap server
```
