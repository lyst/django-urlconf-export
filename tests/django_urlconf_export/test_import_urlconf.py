import pytest
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
