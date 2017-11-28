#!/usr/bin/env python

from setuptools import setup

if __name__ == '__main__':
    setup(
        name="sentaku",
        use_scm_version=True,
        author="RonnyPfannschmidt",
        author_email="opensource@ronnypfannschmidt.de",
        description="variadic ux implementation for testing",
        license="MPLv2",
        keywords=["testing"],
        url="https://github.com/RonnyPfannschmidt/Sentaku",
        packages=["sentaku"],
        package_dir={'': 'src'},
        setup_requires=[
            'setuptools_scm',
        ],
        install_requires=[
            'attrs >= 16.3.0',
            'reg >= 0.10',
            'dectate >= 0.12',
            'importscan',
        ],
        extras_require={
            'test': ['pytest'],
            'examples': ['selenium'],
        },
        classifiers=[
            "Topic :: Utilities",
            "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Intended Audience :: Developers",
            "Development Status :: 4 - Beta",
        ])
