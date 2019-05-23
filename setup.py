from distutils.core import setup

from pkg_resources import parse_requirements
from setuptools import find_packages

with open("requirements.txt") as f:
    REQUIREMENTS = [str(req) for req in parse_requirements(f.read())]

with open("requirements-dev.txt") as f:
    REQUIREMENTS_DEV = [str(req) for req in parse_requirements(f.read())]

setup(
    name="gmail-img-dl",
    version="0.0.3",
    description="CLI tool for retrieving image attachments from GMail messages (specifically from Reolink security cameras)",
    author="Mateusz Korzeniowski",
    author_email="emkor93@gmail.com",
    url="https://github.com/emkor/gmail-img-dl",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    extras_require={
        'dev': REQUIREMENTS_DEV
    },
    entry_points={"console_scripts": [
        "gmail-dl = gmail_img_dl.main:cli_main"
    ]}
)
