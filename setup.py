# -*- coding: utf-8 -*-
from os import path

from setuptools import find_packages, setup

# read the contents of the README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="django-urlconf-export",
    version="1.1.1",
    description="Make URLs for your website from anywhere.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lyst Ltd.",
    author_email="devs@lyst.com",
    package_dir={"": "src"},
    packages=find_packages("src", include=["django_urlconf_export", "django_urlconf_export.*"]),
    zip_safe=False,
    install_requires=["django", "requests"],
    python_requires=">=3.6",
    url="https://github.com/lyst/django-urlconf-export",
)
