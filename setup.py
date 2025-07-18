from setuptools import setup, find_packages

setup(
    name="goldfaish",
    version="0.1.0",
    description="",
    author="Greg Izatt",
    author_email="",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
    include_package_data=True,
    license="MIT",
    entry_points={
        'console_scripts': [
            'run-matchup=goldfaish.run_matchup:main',
        ],
    },
)
