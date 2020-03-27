import sys
import types

import django
import pytest
from django.conf import settings
from django.urls import clear_url_caches


@pytest.fixture()
def mock_urlconf_module():
    # Create a mock module to store some urlconf
    mock_urlconf_module = types.ModuleType(
        "mock_urlconf_module", "Simulates a urls module we want to export or import"
    )
    sys.modules["mock_urlconf_module"] = mock_urlconf_module

    # Make module reference available to the test
    yield mock_urlconf_module

    # After the test, remove the mock module from sys.modules
    del sys.modules["mock_urlconf_module"]
    # Also clear the Django's URLconf caches because
    # 'mock_urlconf_module' is different for each test
    clear_url_caches()


@pytest.fixture()
def mock_included_module():
    # Make a mock included urlconf module
    mock_included_module = types.ModuleType("mock_included_module")
    sys.modules["mock_included_module"] = mock_included_module

    # Make module reference available to the test
    yield mock_included_module

    # After the test, remove the mock module from sys.modules
    del sys.modules["mock_included_module"]
    # Also clear the Django's URLconf caches because
    # 'mock_included_module' is different for each test
    clear_url_caches()


def pytest_configure():
    settings.configure(
        USE_I18N=True,
        USE_L10N=True,
        LANGUAGE_CODE="en-us",
        SECRET_KEY="aifbc",
        ROOT_URLCONF="mock_root_urlconf",
    )

    django.setup()
