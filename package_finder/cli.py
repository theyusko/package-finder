import argparse
import sys
from .searcher import PackageSearcher, print_package_info

def main():
    parser = argparse.ArgumentParser(description='Search for packages across multiple repositories')
    parser.add_argument('package_names', nargs='+', help='Names of packages to search for')
    args = parser.parse_args()
    
    searcher = PackageSearcher()
    results = searcher.search_packages(args.package_names)
    
    for package_name, package_results in results.items():
        if package_results:
            print(f"\nFound '{package_name}' in {len(package_results)} repositories:")
            for result in package_results:
                print_package_info(result)
        else:
            print(f"\n❌ Package '{package_name}' was not found in any repository.")
    
    # Return non-zero if any package wasn't found
    return 0 if all(bool(results[pkg]) for pkg in args.package_names) else 1

if __name__ == "__main__":
    sys.exit(main())