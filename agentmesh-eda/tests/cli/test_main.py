from unittest.mock import patch
from loguru import logger
from agentmesh.cli import main


def test_cli_start_agent(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=main.argparse.Namespace(command="start-agent"),
    ):
        with patch.object(logger, "info") as mock_info:
            main.main()
            mock_info.assert_any_call("CLI command received: start-agent")
            mock_info.assert_any_call("Starting agent (Placeholder)")


def test_cli_send_message(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=main.argparse.Namespace(command="send-message"),
    ):
        with patch.object(logger, "info") as mock_info:
            main.main()
            mock_info.assert_any_call("CLI command received: send-message")
            mock_info.assert_any_call("Sending message (Placeholder)")


def test_cli_unknown_command(capsys):
    with patch(
        "argparse.ArgumentParser.parse_args",
        return_value=main.argparse.Namespace(command="unknown-command"),
    ):
        with patch.object(logger, "warning") as mock_warning:
            main.main()
            mock_warning.assert_called_once_with("Unknown command: unknown-command")
