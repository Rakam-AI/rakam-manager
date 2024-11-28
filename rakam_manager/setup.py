from setuptools import setup, find_packages

setup(
    name="rakam_manager",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "PyYAML",
        "pytest",
        "pytest-mock",
        "typeguard",  # Add dependencies here
    ],
    entry_points={
        "console_scripts": [
            "rakam_manager=rakam_manager.cli:cli",
        ],
    },
)
