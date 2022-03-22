#!/usr/bin/env python3
from setuptools import setup, find_packages
import versioneer


desc = """
qrmagic: CLI and Web tools for handling field collection metadata.
"""

with open("requirements.txt") as fh:
    install_requires = [req.strip() for req in fh]

setup(
    name="qrmagic",
    packages=find_packages(),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    setup_requires=["versioneer",],
    install_requires=install_requires,
    include_package_data=True,
    data_files=['requirements.txt'],
    description=desc,
    entry_points='''
        [console_scripts]
        qrmagic-detect=qrmagic.scanimages:climain
        qrmagic-labelprint=qrmagic.labelmaker:main
    ''',
    author="Kevin Murray",
    author_email="foss@kdmurray.id.au",
    url="https://gitlab.com/kdm9",
    keywords=["qrcode", "fieldwork",],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
