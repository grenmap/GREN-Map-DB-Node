# Shared Storage with Redis

We are using Redis to keep ephemeral information shared by the app and task runner containers: the contents of files to be imported and the GraphQL cache.

The server's app container receives files to be imported: when a user uploads them on the admin page, when the server receives them on the grenml_import API endpoint or when a peer GRENMap server responds to a polling request.

The app container writes a file to be imported to Redis as a key-value pair. Django-Q then triggers a worker process in the task runner container. The process reads the file from Redis, then deletes its corresponding entry.

After processing all instances of each network element entity (node, link and institution), the worker process in the task runner runs the GraphQL query that compiles the visualization data required by the Angular web front-end. The worker writes each query result to Redis.

When the app container receives a visualization request, which comes after a client machine loads the Angular front-end, it reads the GraphQL query result from Redis and uses it to build the response.
