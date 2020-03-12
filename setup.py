# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="django-urlconf-export",
    version="1.0.0",
    description="Make URLs for your website from anywhere.",
    long_description="Exports your Django website URLconf in a JSON format, and imports it in other services.",
    author="Lyst Ltd.",
    author_email="devs@lyst.com",
    package_dir={"": "src"},
    packages=find_packages("src", include=["django_urlconf_export", "django_urlconf_export.*"]),
    zip_safe=False,
    install_requires=["django", "requests"],
    python_requires=">=3.6",
    url="https://github.com/lyst/django-urlconf-export",
)
