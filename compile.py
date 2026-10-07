import sys

from source.printing import *
from source.main import *

def print_help():
    print("Usage: python compile.py [file] [arguments]\n")
    print(f"\t[file]                 the .lss file")
    print("")
    print("Optional arguments:\n")
    print("\t--help                  prints this help text")
    print("\t--verbose               output debug info")
    print("\t--output <folder>       output folder (default: build)")
    print("\t--name <name>           override the theme name from @theme")

def get_option(name: str):
    if name in sys.argv:
        index = sys.argv.index(name)
        if index + 1 >= len(sys.argv):
            print_error(f"Missing value for {name}")
            print_help()
            sys.exit(1)
        return sys.argv[index + 1]
    return None

if __name__ == "__main__":
    if "--help" in sys.argv:
        print_help()
        sys.exit()
    if len(sys.argv) < 2:
        print_error("Missing argument")
        print_help()
        sys.exit()
    is_verbose = "--verbose" in sys.argv
    output_folder = get_option("--output") or "build"
    main(sys.argv[1], is_verbose, output_folder, get_option("--name"))
