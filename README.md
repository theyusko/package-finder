# Universal Package Finder

## Overview

Universal Package Finder is a powerful, cross-repository search tool. It searches for packages across the repositories below ( and more repositories can be added):

- Bioconda
- Anaconda
- PyPI
- Bioconductor
- Conda-forge
- CRAN
- rOpenSci
- Posit Package Manager
- BioLib
- Galaxy Tool Shed
- Docker Hub
- GitHub Container Registry
- Homebrew

Future repositories to include: 
- Biocontainers (already seems to be covered by Docker but better to have explicit support)
- Julia Package Registry (https://julialang.org/packages/) and Pkg.jl package manager
- CPAN (Comprehensive Perl Archive Network)
- crates.io (Rust's package registry)
- Spack (HPC package manager)
- EasyBuild (Scientific software management)
- Guix-Bio (GNU Guix for bioinformatics)
- Chocolatey (Windows package manager)
- Linuxbrew (already partially covered by Homebrew)
- Maven Central (for Java/Scala bioinformatics tools)

## Features

- 🔍 Multi-repository package search
- 📦 Comprehensive package information retrieval
- 🏷️ Version tracking and display
- 🧵 Threading support detection
- 🌐 Wide range of repositories supported

## Installation

### Prerequisites

- Python 3.8+
- pip
- Required Python libraries (installed automatically):
  - requests
  - beautifulsoup4
  - typing

### Install from Source

```bash
# Clone the repository
git clone https://github.com/theyusko/package-finder.git
cd package-finder

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

Search for packages across multiple repositories:

```bash
# Basic usage
package-finder search qsmooth

# Search for multiple packages
package-finder search numpy pandas scipy
```

### Python Module

```python
from package_finder import PackageSearcher

# Create a searcher
searcher = PackageSearcher()

# Search for a single package
results = searcher.search_package('fastqc')

# Search for multiple packages
results = searcher.search_packages(['qsmooth', 'fastqc'])

# Print results
for package_name, package_info_list in results.items():
    for package_info in package_info_list:
        print(f"Package: {package_info.name}")
        print(f"Repository: {package_info.repository}")
        print(f"Versions: {package_info.versions}")
```

## Example Output

```
Searching for 3 packages across 13 repositories...

Found 'fastqc' in 4 repositories:
✅ Package 'fastqc' found in Bioconda!
URL: https://anaconda.org/bioconda/fastqc
Description: A quality control tool for high throughput sequence data.
Version counts: 3 major.minor, 10 total
All versions grouped by Major.Minor: {0.10.1}, {0.11.2, 0.11.3, 0.11.4, 0.11.5, 0.11.6, 0.11.7, 0.11.8, 0.11.9}, {0.12.1}
License: GPL >=3
Threading: No explicit support found
...
```

## Configuration

### Customizing Repositories

You can customize the repositories searched by creating a custom `PackageSearcher`:

```python
from package_finder import PackageSearcher, PyPIRepository, BiocondaRepository

# Create a searcher with only specific repositories
custom_searcher = PackageSearcher(repositories=[
    PyPIRepository(),
    BiocondaRepository()
])
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Ecem İlgün - ecem.ilgun@bilkent.edu.tr
