import mock
import pytest
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.test import override_settings
from django.urls import LocalePrefixPattern, URLResolver, include, path, re_path
from django.utils.functional import lazy
from django.utils.translation import get_language
from django.views import View

from django_urlconf_export import export_urlconf


def test_export_route(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = [path("login/", View.as_view(), name="login")]
    assert export_urlconf.as_json("mock_urlconf_module") == [{"route": "login/", "name": "login"}]


def test_export_regex(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = [
        # 'url' is just an alias for 're_path'
        url(r"^login/$", View.as_view(), name="login"),
        re_path(r"^logout/$", View.as_view(), name="logout"),
    ]
    assert export_urlconf.as_json("mock_urlconf_module") == [
        {"regex": "^login/$", "name": "login"},
        {"regex": "^logout/$", "name": "logout"},
    ]


def test_export_include(mock_urlconf_module, mock_included_module):
    # Setup urls to include
    mock_included_module.urlpatterns = [
        url(r"^red/$", View.as_view(), name="red"),
        url(r"^blue/$", View.as_view(), name="blue"),
    ]

    mock_urlconf_module.urlpatterns = [url(r"^colors/", include("mock_included_module"))]
    assert export_urlconf.as_json("mock_urlconf_module") == [
        {
            "regex": "^colors/",
            "namespace": None,
            "app_name": None,
            "includes": [{"regex": "^red/$", "name": "red"}, {"regex": "^blue/$", "name": "blue"}],
        }
    ]


@pytest.mark.parametrize(
    "app_name, namespace, expected_app_name, expected_namespace",
    [
        (None, None, None, None),
        ("app", "ns", "app", "ns"),
        # Setting app_name only will set namespace = app_name
        ("app", None, "app", "app"),
        # NOTE: setting namespace only will cause an error
    ],
)
def test_export_include_with_namespace(
    mock_urlconf_module,
    mock_included_module,
    app_name,
    namespace,
    expected_app_name,
    expected_namespace,
):
    # Maybe set app_name on included urls module
    if app_name:
        mock_included_module.app_name = app_name

    # Setup urls to include
    mock_included_module.urlpatterns = [
        url(r"^red/$", View.as_view(), name="red"),
        url(r"^blue/$", View.as_view(), name="blue"),
    ]

    # Maybe set a namespace for the included urls
    if namespace:
        mock_urlconf_module.urlpatterns = [
            url(r"^colors/", include("mock_included_module", namespace=namespace))
        ]
    else:
        mock_urlconf_module.urlpatterns = [url(r"^colors/", include("mock_included_module"))]

    assert export_urlconf.as_json("mock_urlconf_module") == [
        {
            "regex": "^colors/",
            "namespace": expected_namespace,
            "app_name": expected_app_name,
            "includes": [{"regex": "^red/$", "name": "red"}, {"regex": "^blue/$", "name": "blue"}],
        }
    ]


def test_export_locale_prefix_pattern(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = i18n_patterns(url(r"^$", View.as_view(), name="index"))
    assert export_urlconf.as_json("mock_urlconf_module") == [
        {
            "isLocalePrefix": True,
            "classPath": "django.urls.resolvers.LocalePrefixPattern",
            "includes": [{"regex": "^$", "name": "index"}],
        }
    ]


# You can use a subclass of LocalePrefixPattern
# and Urls Export still works
class CustomLocalePrefixPattern(LocalePrefixPattern):
    pass


def test_export_custom_locale_prefix_pattern_class(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = [
        URLResolver(CustomLocalePrefixPattern(), [url(r"^$", View.as_view(), name="index")])
    ]
    assert export_urlconf.as_json("mock_urlconf_module") == [
        {
            "isLocalePrefix": True,
            "classPath": "tests.django_urlconf_export.test_export_urlconf.CustomLocalePrefixPattern",
            "includes": [{"regex": "^$", "name": "index"}],
        }
    ]


_mock_supported_languages = [
    ("en", {"bidi": False, "code": "en", "name": "English", "name_local": "English"}),
    (
        "en-gb",
        {
            "bidi": False,
            "code": "en-gb",
            "name": "British English",
            "name_local": "British English",
        },
    ),
    ("fr", {"bidi": False, "code": "fr", "name": "French", "name_local": "français"}),
]


def _get_color_url_pattern():
    return {"en": r"^color/$", "en-gb": r"^colour/$", "fr": r"^couleur/$"}[get_language()]


@override_settings(LANGUAGES=_mock_supported_languages)
def test_export_multi_language(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = [
        url(lazy(_get_color_url_pattern, str)(), View.as_view(), name="color")
    ]
    assert export_urlconf.as_json("mock_urlconf_module", language_without_country=False) == [
        {"regex": {"en": "^color/$", "en-gb": "^colour/$", "fr": "^couleur/$"}, "name": "color"}
    ]


@override_settings(LANGUAGES=_mock_supported_languages)
def test_export_multi_language_without_country(mock_urlconf_module):
    mock_urlconf_module.urlpatterns = [
        url(lazy(_get_color_url_pattern, str)(), View.as_view(), name="color")
    ]
    assert export_urlconf.as_json("mock_urlconf_module", language_without_country=True) == [
        {"regex": {"en": "^color/$", "fr": "^couleur/$"}, "name": "color"}
    ]


@pytest.mark.parametrize(
    "whitelist, blacklist, expected_url_names",
    [
        # With no blacklist or whitelist, all url names and included namespaces will be exported
        (set(), set(), {"public-a", "public-b", "admin", "secret-1", "secret-2", "db-edit"}),
        # Blacklisted names / namespaces are excluded
        (set(), {"db-edit"}, {"public-a", "public-b", "admin", "secret-1", "secret-2"}),
        # If an included namespace is blacklisted, exclude child urls too
        (set(), {"admin"}, {"public-a", "public-b"}),
        # Blacklist entries are regexes
        (set(), {"secret-."}, {"public-a", "public-b", "admin", "db-edit"}),
        # If whitelist specified, only include these names / namespaces
        ({"public-a"}, set(), {"public-a"}),
        # Whitelist entries are regexes
        ({"public-."}, set(), {"public-a", "public-b"}),
        # Blacklist overrides whitelist
        ({"public-."}, {"public-a"}, {"public-b"}),
        # If you only whitelist a namespace but not any of its included urls
        # you get no results because the namespace is empty
        ({"admin"}, set(), set()),
        # If you only whitespace included urls but not their namespace
        # you also get no results
        ({"secret-."}, set(), set()),
        # You need to whitelist both the namespace and any included url names you want to export
        ({"admin", "secret-."}, set(), {"admin", "secret-1", "secret-2"}),
    ],
)
def test_whitelist_and_blacklist(
    whitelist, blacklist, expected_url_names, mock_urlconf_module, mock_included_module
):
    mock_included_module.app_name = "admin"
    mock_included_module.urlpatterns = [
        url(r"^secret-1/$", View.as_view(), name="secret-1"),
        url(r"^secret-2/$", View.as_view(), name="secret-2"),
        url(r"^db-edit/$", View.as_view(), name="db-edit"),
    ]

    mock_urlconf_module.urlpatterns = [
        url(r"^public-a/$", View.as_view(), name="public-a"),
        url(r"^public-b/$", View.as_view(), name="public-b"),
        url(r"^admin/$", include("mock_included_module", namespace="admin")),
    ]
    assert (
        export_urlconf.get_all_allowed_url_names(
            "mock_urlconf_module", whitelist=whitelist, blacklist=blacklist
        )
        == expected_url_names
    )


@mock.patch("django_urlconf_export.export_urlconf._get_json_urlpatterns")
@mock.patch("django.urls.get_resolver")
@override_settings()
def test_defaults_to_root_urlconf(mock_get_resolver, mock_get_json_urlpatterns):
    # simulate absence of these settings
    del settings.URLCONF_EXPORT_ROOT_URLCONF
    del settings.URLCONF_EXPORT_WHITELIST
    del settings.URLCONF_EXPORT_BLACKLIST
    del settings.URLCONF_EXPORT_LANGUAGE_WITHOUT_COUNTRY

    mock_resolver = mock.Mock()
    mock_get_resolver.return_value = mock_resolver

    export_urlconf.as_json()

    mock_get_resolver.assert_called_once_with(settings.ROOT_URLCONF)
    mock_get_json_urlpatterns.assert_called_once_with(mock_resolver, None, None, False)


@mock.patch("django_urlconf_export.export_urlconf._get_json_urlpatterns")
@mock.patch("django.urls.get_resolver")
@override_settings(
    URLCONF_EXPORT_ROOT_URLCONF="path.to.urlconf",
    URLCONF_EXPORT_WHITELIST=["whitelisted-url-name"],
    URLCONF_EXPORT_BLACKLIST=["blacklisted-url-name"],
    URLCONF_EXPORT_LANGUAGE_WITHOUT_COUNTRY=True,
)
def test_can_use_django_settings(mock_get_resolver, mock_get_json_urlpatterns):
    mock_resolver = mock.Mock()
    mock_get_resolver.return_value = mock_resolver

    export_urlconf.as_json()

    mock_get_resolver.assert_called_once_with("path.to.urlconf")
    mock_get_json_urlpatterns.assert_called_once_with(
        mock_resolver, ["whitelisted-url-name"], ["blacklisted-url-name"], True
    )
