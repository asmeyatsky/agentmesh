Disaster Recovery (DR)
======================

The Disaster Recovery (DR) module provides services for backing up and recovering the state of the AgentMesh EDA platform.

Core Components
---------------

- **Backup Service:** A service for creating backups of the platform's state.
- **Recovery Service:** A service for recovering the platform's state from a backup.

Usage
-----

To use the DR module, you can use the `BackupService` to create a backup and the `RecoveryService` to restore from a backup.

.. code-block:: python

    from agentmesh.dr.backup_service import BackupService
    from agentmesh.dr.recovery_service import RecoveryService

    backup_service = BackupService()
    backup_id = backup_service.create_backup()

    recovery_service = RecoveryService()
    recovery_service.recover(backup_id)
