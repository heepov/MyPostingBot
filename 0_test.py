import logging
from os import getenv
from file_service import load_file, save_file
from utils import files_cleaner


def main() -> None:
    files_cleaner()


if __name__ == "__main__":
    main()
