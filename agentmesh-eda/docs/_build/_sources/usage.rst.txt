Usage Instructions
==================

This section provides instructions on how to set up and use the AgentMesh EDA solution.

Setting up the Environment
--------------------------

1.  **Prerequisites:**

    *   `Docker` and `Docker Compose`: Ensure Docker Desktop is installed and running.
    *   `Python 3.9+` and `pip` (or `poetry` if preferred for dependency management).

2.  **Clone the Repository:**

    .. code-block:: bash

        git clone <repository_url>
        cd agentmesh-eda

3.  **Build and Run Docker Containers:**

    The project uses Docker Compose to manage its services, including the AgentMesh application, a NATS messaging server, and a PostgreSQL database.

    .. code-block:: bash

        docker-compose up --build -d

    This command will:

    *   Build the `agentmesh` Docker image.
    *   Start the `agentmesh` container.
    *   Start the `nats` messaging server container.
    *   Start the `postgres` database container.

    You can check the status of the running containers with `docker-compose ps`.

Using the CLI
-------------

The AgentMesh EDA CLI tool allows you to interact with the system from your terminal. You can execute CLI commands using `docker-compose exec agentmesh python -m agentmesh.cli.main <command>`.

**Examples:**

1.  **Create a new tenant:**

    .. code-block:: bash

        docker-compose exec agentmesh python -m agentmesh.cli.main tenant create mytenant

2.  **List all tenants:**

    .. code-block:: bash

        docker-compose exec agentmesh python -m agentmesh.cli.main tenant list

3.  **Check system status:**

    .. code-block:: bash

        docker-compose exec agentmesh python -m agentmesh.cli.main status

4.  **View a message by ID (placeholder for future implementation):**

    .. code-block:: bash

        docker-compose exec agentmesh python -m agentmesh.cli.main message view <message_id>

Using the UI
------------

The AgentMesh EDA provides a simple web-based user interface for monitoring and managing the system.

1.  **Access the UI:**

    Once the Docker containers are running, you can access the UI in your web browser at:

    `http://localhost:5000`

2.  **Available Pages:**

    *   **Home (`/`):** Provides links to other sections of the UI.
    *   **Tenants (`/tenants`):** View existing tenants and create new ones.
    *   **System Status (`/status`):** Check the overall health of the system.
    *   **Messages (`/messages`):** View messages processed by the system.
