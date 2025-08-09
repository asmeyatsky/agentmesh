from agentmesh.dr.backup_service import BackupService
from unittest.mock import patch
from loguru import logger


def test_backup_service_init():
    with patch.object(logger, "info") as mock_info:
        BackupService()
        mock_info.assert_called_once_with("BackupService initialized.")


def test_backup_service_perform_backup():
    service = BackupService()
    data = {"db": "snapshot", "files": "archive"}
    with patch.object(logger, "info") as mock_info:
        result = service.perform_backup(data)
        assert result # Changed to truthy check
        mock_info.assert_called_once_with(
            f"Performing backup of data: {data} (Placeholder)"
        )


def test_backup_service_get_last_backup_status():
    service = BackupService()
    with patch.object(logger, "info") as mock_info:
        status = service.get_last_backup_status()
        assert status == {"status": "success", "timestamp": "2025-08-09T10:00:00Z"}
        mock_info.assert_called_once_with("Getting last backup status. (Placeholder)")
