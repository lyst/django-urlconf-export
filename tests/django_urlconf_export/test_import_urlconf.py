import sys

import mock
import pytest
from django.test import override_settings
from django.urls import LocalePrefixPattern, reverse
from django.utils import translation

from django_urlconf_export import import_urlconf

from tests.django_urlconf_export.test_export_urlconf import CustomLocalePrefixPattern


def test_import_route(mock_urlconf_module):
    import_urlconf.from_json([{"route": "login/", "name": "login"}], urlconf="mock_urlconf_module")
    assert reverse("login", urlconf="mock_urlconf_module") == "/login/"


def test_import_regex(mock_urlconf_module):
    import_urlconf.from_json(
        [{"regex": "^login/$", "name": "login"}], urlconf="mock_urlconf_module"
    )
    assert reverse("login", urlconf="mock_urlconf_module") == "/login/"


def test_import_include(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                "regex": "^colors/",
                "namespace": None,
                "app_name": None,
                "includes": [
                    {"regex": "^red/$", "name": "red"},
                    {"regex": "^blue/$", "name": "blue"},
                ],
            }
        ],
        urlconf="mock_urlconf_module",
    )
    assert reverse("red", urlconf="mock_urlconf_module") == "/colors/red/"
    assert reverse("blue", urlconf="mock_urlconf_module") == "/colors/blue/"


def test_import_include_with_namespace(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                "regex": "^colors/",
                "namespace": "colors_ns",
                "app_name": "colors_app",
                "includes": [
                    {"regex": "^red/$", "name": "red"},
                    {"regex": "^blue/$", "name": "blue"},
                ],
            }
        ],
        urlconf="mock_urlconf_module",
    )
    assert reverse("colors_ns:red", urlconf="mock_urlconf_module") == "/colors/red/"
    assert reverse("colors_ns:blue", urlconf="mock_urlconf_module") == "/colors/blue/"


def test_import_locale_prefix_pattern(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                "isLocalePrefix": True,
                "classPath": "django.urls.resolvers.LocalePrefixPattern",
                "includes": [{"regex": "^$", "name": "index"}],
            }
        ],
        urlconf="mock_urlconf_module",
    )
    with translation.override("en"):
        assert reverse("index", urlconf="mock_urlconf_module") == "/en/"
    with translation.override("fr"):
        assert reverse("index", urlconf="mock_urlconf_module") == "/fr/"


@pytest.mark.parametrize(
    "class_path, expected_class",
    [
        ("django.urls.resolvers.LocalePrefixPattern", LocalePrefixPattern),
        (
            "tests.django_urlconf_export.test_export_urlconf.CustomLocalePrefixPattern",
            CustomLocalePrefixPattern,
        ),
    ],
)
def test_import_custom_locale_prefix_pattern_class(class_path, expected_class):
    django_urlpatterns = import_urlconf._get_django_urlpatterns(
        [
            {
                "isLocalePrefix": True,
                "classPath": class_path,
                "includes": [{"regex": "^$", "name": "index"}],
            }
        ]
    )
    locale_prefix = django_urlpatterns[0]
    assert locale_prefix.pattern.__class__ == expected_class


def test_import_multi_language(mock_urlconf_module):
    import_urlconf.from_json(
        [{"regex": {"en": "^color/$", "en-gb": "^colour/$", "fr": "^couleur/$"}, "name": "color"}],
        urlconf="mock_urlconf_module",
    )
    with translation.override("en"):
        assert reverse("color", urlconf="mock_urlconf_module") == "/color/"
    with translation.override("en-gb"):
        assert reverse("color", urlconf="mock_urlconf_module") == "/colour/"
    with translation.override("fr"):
        assert reverse("color", urlconf="mock_urlconf_module") == "/couleur/"


def test_import_multi_language_without_country(mock_urlconf_module):
    import_urlconf.from_json(
        [{"regex": {"en": "^color/$"}, "name": "color"}], urlconf="mock_urlconf_module"
    )
    with translation.override("en"):
        assert reverse("color", urlconf="mock_urlconf_module") == "/color/"
    with translation.override("en-gb"):
        # There's no 'en-gb' value so if will use the 'en' value
        assert reverse("color", urlconf="mock_urlconf_module") == "/color/"


# The tests below use these constants
METHOD_ARGUMENT = "method_argument"
LIBRARY_SETTING = "library_setting"
ROOT_SETTING = "root_setting"
POSSIBLE_CREATED_MODULES = [METHOD_ARGUMENT, LIBRARY_SETTING, ROOT_SETTING]


@pytest.fixture()
def cleanup_created_modules():
    yield
    for urlconf in POSSIBLE_CREATED_MODULES:
        if sys.modules.get(urlconf):
            del sys.modules[urlconf]


@pytest.mark.parametrize(
    "method_argument, library_setting, root_setting, expected_created_module",
    [
        # settings.ROOT_URLCONF is the default
        (None, None, ROOT_SETTING, ROOT_SETTING),
        # settings.URLCONF_IMPORT_ROOT_URLCONF overrides settings.ROOT_URLCONF
        (None, LIBRARY_SETTING, ROOT_SETTING, LIBRARY_SETTING),
        # An argument on the method overrides all settings
        (METHOD_ARGUMENT, LIBRARY_SETTING, ROOT_SETTING, METHOD_ARGUMENT),
    ],
)
def test_import_will_create_urlconf_module(
    cleanup_created_modules, method_argument, library_setting, root_setting, expected_created_module
):
    with override_settings(URLCONF_IMPORT_ROOT_URLCONF=library_setting, ROOT_URLCONF=root_setting):
        import_urlconf.from_json([{"route": "login/", "name": "login"}], urlconf=method_argument)

    # Check the right module was created and we can use it to make URLs
    assert sys.modules.get(expected_created_module)
    assert reverse("login", urlconf=expected_created_module) == "/login/"

    # Check no other modules were created
    other_possible_created_modules = [
        m for m in POSSIBLE_CREATED_MODULES if m != expected_created_module
    ]
    for module_name in other_possible_created_modules:
        assert not sys.modules.get(module_name)


@override_settings(URLCONF_IMPORT_ROOT_URLCONF=None, ROOT_URLCONF=None)
def test_import_will_raise_if_no_urlconf_module_specified(cleanup_created_modules):
    with pytest.raises(ValueError):
        import_urlconf.from_json([{"route": "login/", "name": "login"}])


def test_import_will_overwrite_existing_urlconf(cleanup_created_modules):
    import_urlconf.from_json([{"route": "login/", "name": "login"}], urlconf=METHOD_ARGUMENT)
    assert reverse("login", urlconf=METHOD_ARGUMENT) == "/login/"

    import_urlconf.from_json([{"route": "new-login/", "name": "login"}], urlconf=METHOD_ARGUMENT)
    assert reverse("login", urlconf=METHOD_ARGUMENT) == "/new-login/"


@mock.patch("django.setup")
@mock.patch("django.conf.settings")
def test_init_django_with_default_settings(mock_django_settings, mock_django_setup):
    mock_django_settings.configured = False
    mock_django_settings.configure = mock.Mock()

    import_urlconf.init_django()

    mock_django_settings.configure.assert_called_once_with(
        USE_I18N=True,
        USE_L10N=True,
        LANGUAGE_CODE="en-us",
        SECRET_KEY="not-a-very-secret-key-but-we-need-something-here",
        ROOT_URLCONF="imported_urlconf",
    )
    mock_django_setup.assert_called_once_with()


@mock.patch("django.setup")
@mock.patch("django.conf.settings")
def test_init_django_with_overridden_settings(mock_django_settings, mock_django_setup):
    mock_django_settings.configured = False
    mock_django_settings.configure = mock.Mock()

    import_urlconf.init_django(ROOT_URLCONF="another_urlconf_module", OTHER_SETTING="foo")

    mock_django_settings.configure.assert_called_once_with(
        USE_I18N=True,
        USE_L10N=True,
        LANGUAGE_CODE="en-us",
        SECRET_KEY="not-a-very-secret-key-but-we-need-something-here",
        ROOT_URLCONF="another_urlconf_module",
        OTHER_SETTING="foo",
    )
    mock_django_setup.assert_called_once_with()


@mock.patch("django.setup")
@mock.patch("django.conf.settings")
def test_init_django_when_already_initialized(mock_django_settings, mock_django_setup):
    mock_django_settings.configured = True
    mock_django_settings.configure = mock.Mock()

    import_urlconf.init_django()

    assert not mock_django_settings.configure.called
    assert not mock_django_setup.called


@mock.patch("django.setup")
@mock.patch("django.conf.settings")
def test_init_django_with_overridden_settings_when_already_initialized(
    mock_django_settings, mock_django_setup
):
    mock_django_settings.configured = True
    mock_django_settings.configure = mock.Mock()

    # Django has already been initialized with this setting
    mock_django_settings.SOME_SETTING = "foo"

    # If we initialize again with the same setting, nothing happens
    import_urlconf.init_django(SOME_SETTING="foo")

    # If we initialize again with the setting as a different value, error.
    with pytest.raises(ValueError):
        import_urlconf.init_django(SOME_SETTING="bar")

    # If we initialize again with an additional setting, error.
    with pytest.raises(ValueError):
        import_urlconf.init_django(SOME_SETTING="foo", OTHER_SETTING="baz")

    assert not mock_django_settings.configure.called
    assert not mock_django_setup.called
