Message Abstraction Layer (MAL)
===============================

The Message Abstraction Layer (MAL) provides a unified interface for interacting with various messaging systems. It abstracts the complexities of different messaging protocols and provides a consistent API for sending and receiving messages.

Core Components
---------------

- **Universal Message:** A standardized message format that supports JSON, Avro, Protobuf, and CloudEvents.
- **Multi-Protocol Support:** A unified API that abstracts Kafka, Google Pub/Sub, AWS SNS/SQS, NATS, and Apache Pulsar.
- **Dynamic Routing Engine:** An intelligent message routing engine that routes messages based on content, agent capabilities, and system load.
- **Schema Registry:** A centralized schema management system with evolution and compatibility checking.

Usage
-----

To use the MAL, you first need to create a `MessageRouter` instance. Then, you can use the `route_message` method to send a `UniversalMessage`.

.. code-block:: python

    from agentmesh.mal.router import MessageRouter
    from agentmesh.mal.message import UniversalMessage

    router = MessageRouter()
    message = UniversalMessage(
        payload={"key": "value"},
        routing={"targets": ["nats:my.subject"]}
    )
    await router.route_message(message)
