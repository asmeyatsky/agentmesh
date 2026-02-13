from unittest.mock import patch, MagicMock
from loguru import logger
from agentmesh.cli import main
import argparse


def test_cli_tenant_create(capsys):
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                command="tenant", tenant_command="create", name="my-tenant"
            ),
        ),
        patch("agentmesh.cli.main.SessionLocal") as mock_session_local,
        patch.object(logger, "info") as mock_info,
    ):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        main.main()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_info.assert_called_once_with("Tenant 'my-tenant' created successfully.")
        mock_session.close.assert_called_once()


def test_cli_tenant_create_existing(capsys):
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                command="tenant", tenant_command="create", name="my-tenant"
            ),
        ),
        patch("agentmesh.cli.main.SessionLocal") as mock_session_local,
        patch.object(logger, "error") as mock_error,
    ):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = (
            MagicMock()
        )  # Simulate existing tenant

        main.main()

        mock_error.assert_called_once_with(
            "Tenant with name 'my-tenant' already exists."
        )
        mock_session.close.assert_called_once()


def test_cli_tenant_list(capsys):
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(command="tenant", tenant_command="list"),
        ),
        patch("agentmesh.cli.main.SessionLocal") as mock_session_local,
        patch("builtins.print") as mock_print,
    ):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_tenant1 = MagicMock(name="tenant1")
        mock_tenant2 = MagicMock(name="tenant2")
        mock_session.query.return_value.all.return_value = [mock_tenant1, mock_tenant2]

        main.main()

        mock_print.assert_any_call("tenant1")
        mock_print.assert_any_call("tenant2")
        mock_session.close.assert_called_once()


def test_cli_tenant_list_empty(capsys):
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(command="tenant", tenant_command="list"),
        ),
        patch("agentmesh.cli.main.SessionLocal") as mock_session_local,
        patch.object(logger, "info") as mock_info,
    ):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.all.return_value = []

        main.main()

        mock_info.assert_called_once_with("No tenants found.")
        mock_session.close.assert_called_once()


def test_cli_status(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(command="status"),
    ):
        with patch.object(logger, "info") as mock_info:
            main.main()
            mock_info.assert_called_once_with("System status: OK")


def test_cli_message_view(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            command="message", message_command="view", id="msg123"
        ),
    ):
        with patch.object(logger, "warning") as mock_warning:
            main.main()
            mock_warning.assert_called_once_with(
                "Viewing message with ID: msg123 (Not Implemented)"
            )


def test_cli_no_command(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(command=None),
    ):
        with patch.object(argparse.ArgumentParser, "print_help") as mock_print_help:
            main.main()
            mock_print_help.assert_called_once()
