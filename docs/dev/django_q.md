# Django Q

The GREN Map DB node uses [Django Q](https://django-q.readthedocs.io/en/latest/index.html) for two purposes: to schedule polling events, and to execute long-running tasks asynchronously.

## Topology File Upload

We can import a topology file into the server in two ways: using the admin page and using the `/grenml_import/upload` API endpoint.

The endpoint accepts GRENML files. The GRENMap server verifies an uploaded file conforms to the [GRENML schema](https://github.com/grenmap/GRENML/blob/main/grenml/schemas/grenml.xsd), which is part of the GRENML library source code.

In addition to GRENML files, the upload function in the admin page also accepts [Excel spreadsheets](https://github.com/grenmap/GRENML/blob/main/docs/Sample%20Conversion%20Spreadsheet/GREN_data.v1_0.xlsx).

Both code paths rely on a Django signal triggered by saving the ImportFile model for an uploaded file. The signal handler posts a new task to the queue. The task contains references to the ImportFile model just created and to a function that parses the file and inserts records for network elements in the database.
