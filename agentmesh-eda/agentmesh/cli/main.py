from loguru import logger
import argparse


def main():
    parser = argparse.ArgumentParser(description="AgentMesh EDA CLI Tool")
    parser.add_argument("--version", action="version", version="AgentMesh EDA 0.1.0")
    parser.add_argument(
        "command", help="Command to execute (e.g., 'start-agent', 'send-message')"
    )

    args = parser.parse_args()

    logger.info(f"CLI command received: {args.command}")

    if args.command == "start-agent":
        logger.info("Starting agent (Placeholder)")
    elif args.command == "send-message":
        logger.info("Sending message (Placeholder)")
    else:
        logger.warning(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
