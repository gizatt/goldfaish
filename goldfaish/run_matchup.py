from . import FORGE_BIN_PATH
import subprocess


def main():
    subprocess.run([str(FORGE_BIN_PATH)], check=True)


if __name__ == "__main__":
    main()