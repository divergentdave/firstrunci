from setuptools import setup

setup(
    name="firstrunci",
    version="0.0.1",
    description="Tools to monitor and test the development setup instructions in software documentation",
    author="David Cook",
    author_email="divergentdave@gmail.com",
    packages=["firstrunci"],
    install_requires=[
        "pyyaml",
        "python-vagrant",
    ],
    entry_points = {
        "console_scripts": ["firstrunci=firstrunci:main"]
    }
)
