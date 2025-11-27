from logging_config import configure_logging

logger = configure_logging("omhc")


def main():
    logger.info("Open Mental Health Collective initialized")


if __name__ == "__main__":
    main()
