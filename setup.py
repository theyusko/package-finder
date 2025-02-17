from setuptools import setup, find_packages

setup(
    name="package_finder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3",
        "typing>=3.7.4",
    ],
    entry_points={
        'console_scripts': [
            'package-finder=package_finder.cli:main',
        ],
    },
    author="Ecem İlgün",
    author_email="ecem.ilgun@bilkent.edu.tr",
    description="A tool to search for packages across multiple repositories",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/theyusko/package-finder',
    keywords="package, search, bioconda, pypi, bioconductor",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires=">=3.8",
)