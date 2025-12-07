from source.printing import *
from source.main import *

def print_help():
    print("Usage: python compile.py [file] [arguments]\n")
    print(f"\t[file]                 the .lss file")
    print("")
    print("Optional arguments:\n")
    print("\t--help                  prints this help text")
    print("\t--verbose               output debug info")

if __name__ == "__main__":
    if "--help" in sys.argv:
        print_help()
        sys.exit()
    if len(sys.argv) < 2:
        print_error("Missing argument")
        print_help()
        sys.exit()
    is_verbose = "--verbose" in sys.argv
    main(sys.argv[1], is_verbose)

