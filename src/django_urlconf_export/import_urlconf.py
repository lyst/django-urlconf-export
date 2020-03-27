import json
import sys
import types
from pydoc import locate

import django
import requests
from django import conf as django_conf
from django.urls import LocalePrefixPattern, URLPattern, URLResolver, clear_url_caches
from django.urls.resolvers import RegexPattern, RoutePattern
from django.utils.functional import lazy
from django.utils.translation import get_language

from django_urlconf_export import language_utils
from django_urlconf_export.views.http404 import Http404View


def _get_regex(regex):
    """
    For multi-language URLs, return a lazy string.

    :param regex: string or dict
        Either a regex string, or a dict where keys are languages and values are regex strings.
    :return: string or lazy string
    """
    if isinstance(regex, str):
        return regex
    if isinstance(regex, dict):
        # regex is like {"en": "hello", "fr": "salut"}
        # create a lazy string that returns the regex
        # for the currently selected language
        def _get_pattern():
            language = get_language()
            if regex.get(language):
                return regex[language]
            else:
                # Fallback to language without country
                # e.g. if "en-gb" is not defined, use value for "en"
                language_without_country = language_utils.get_without_country(language)
                return regex[language_without_country]

        return lazy(_get_pattern, str)()
    raise ValueError(f"Invalid regex: {regex}")


def _get_pattern_class_and_regex(json_url):
    """
    Parse JSON URLconf dict, and return the pattern class and regex

    :param json_url: JSON URLconf dict
    :return: tuple(class, string or lazy string)
    """
    regex = json_url.get("regex")
    if regex is not None:
        return RegexPattern, _get_regex(regex)

    route = json_url.get("route")
    if route is not None:
        return RoutePattern, _get_regex(route)

    raise ValueError(f"Invalid json_url: {json_url}")


def _get_django_urlpatterns(json_urlpatterns):
    """
    Parse JSON URLconf, and return a list of Django urlpatterns.

    :param json_urlpatterns: list of JSON URLconf dicts
    :return: list of Django URLResolver and URLPattern objects
    """
    django_urlpatterns = []
    for json_url in json_urlpatterns:
        includes = json_url.get("includes")
        if includes:
            # Make a URLResolver
            included_django_urlpatterns = _get_django_urlpatterns(includes)

            isLocalePrefix = json_url.get("isLocalePrefix")
            if isLocalePrefix:
                # Make a LocalePrefixPattern.
                # Custom sub-classes are allowed.
                LocalePrefixPatternClass = locate(json_url.get("classPath"))
                if not issubclass(LocalePrefixPatternClass, LocalePrefixPattern):
                    raise ValueError(
                        f"Locale prefix class {json_url.get('classPath')} "
                        f"is not a subclass of LocalePrefixPattern"
                    )
                django_url = URLResolver(LocalePrefixPatternClass(), included_django_urlpatterns)

            else:
                # Make an include(...)
                PatternClass, regex = _get_pattern_class_and_regex(json_url)
                pattern = PatternClass(regex, is_endpoint=False)
                django_url = URLResolver(
                    pattern,
                    included_django_urlpatterns,
                    app_name=json_url.get("app_name"),
                    namespace=json_url.get("namespace"),
                )

        else:
            # Make a URLPattern
            name = json_url.get("name")
            PatternClass, regex = _get_pattern_class_and_regex(json_url)
            pattern = PatternClass(regex, name=name, is_endpoint=True)
            # Make a dummy view so the URL Pattern is valid.
            # If this view is ever actually rendered, it will return 404.
            # Note we're also ignoring the kwargs that can be added to url() definitions.
            # These are not used to generate urls, they are just passed to the view.
            django_url = URLPattern(pattern, Http404View.as_view(), name=name)

        django_urlpatterns.append(django_url)
    return django_urlpatterns


def _update_django_urlpatterns_in_module(django_urlpatterns, urlconf):
    """
    Update the Django URLconf in a module.
    Create the module if necessary.

    :param django_urlpatterns: list of Django URLResolver and URLPattern objects
    :param urlconf: string - name of module to save the urlpatterns in
    :return: None
    """
    if urlconf is None:
        urlconf = getattr(django_conf.settings, "URLCONF_IMPORT_ROOT_URLCONF", None)
        if urlconf is None:
            urlconf = getattr(django_conf.settings, "ROOT_URLCONF", None)

    if not urlconf:
        raise ValueError(
            "Urlconf is not defined. You must set settings.ROOT_URLCONF, "
            "or set settings.URLCONF_IMPORT_ROOT_URLCONF, "
            "or specify a urlconf module name when importing urlconf. "
            "You can use any name you like for the urlconf module, and "
            "it will be created if it doesn't already exist."
        )

    if sys.modules.get(urlconf):
        module_already_existed = True
        # Load existing module
        urlconf_module = sys.modules.get(urlconf)
    else:
        module_already_existed = False
        # Create module
        urlconf_module = types.ModuleType(urlconf, "Imported URLs will live in this module")
        sys.modules[urlconf] = urlconf_module

    # Create or overwrite urlpatterns
    urlconf_module.urlpatterns = django_urlpatterns

    # If the module already existed, Django might have cached some URLconf from it
    if module_already_existed:
        clear_url_caches()


def from_json(json_urlpatterns, urlconf=None):
    """
    Import URLconf from a list of JSON dict

    :param json_urlpatterns: list of JSON URLconf dicts
    :param urlconf: string - name of module to import URLconf into
    :return: None
    """
    django_urlpatterns = _get_django_urlpatterns(json_urlpatterns)
    _update_django_urlpatterns_in_module(django_urlpatterns, urlconf)


def from_file(file_path, urlconf=None):
    """
    Import URLconf from a file

    :param file_path: string - location of file containing URLconf JSON
    :param urlconf: string - name of module to import URLconf into
    :return: None
    """
    with open(file_path) as json_file:
        json_urlpatterns = json.load(json_file)
    from_json(json_urlpatterns, urlconf)


def from_uri(uri, urlconf=None):
    """
    Import URLconf downloaded from a URI

    :param uri: string - URI to download URLconf JSON from
    :param urlconf: string - name of module to import URLconf into
    :return: None
    """
    json_urlpatterns = requests.get(uri).json()
    from_json(json_urlpatterns, urlconf)


def init_django(**override_settings):
    """
    When importing URLconf in non-Django services,
    call this helper method to initialize Django.

    :param override_settings: kwargs - non-default Django settings to use
    :return: None
    """
    # If Django was already initialized...
    if django_conf.settings.configured:
        # If we don't care about the settings, do nothing.
        if not override_settings:
            return

        # We did care about the settings.
        # Check the settings are what we want.
        for setting_key, new_setting_value in override_settings.items():
            current_setting_value = getattr(django_conf.settings, setting_key, None)
            if current_setting_value is not None:
                if current_setting_value != new_setting_value:
                    raise ValueError(
                        f"Tried to initialize Django multiple times with different settings. "
                        f"Tried to init with settings.{setting_key} == {repr(new_setting_value)} "
                        f"but Django was already initialized with "
                        f"settings.{setting_key} == {repr(current_setting_value)}"
                    )
        # Django was already initialized and
        # had the settings we wanted, so do nothing.
        return

    # These are the default settings
    django_settings = dict(
        USE_I18N=True,
        USE_L10N=True,
        LANGUAGE_CODE="en-us",
        SECRET_KEY="not-a-very-secret-key-but-we-need-something-here",
        ROOT_URLCONF="imported_urlconf",
    )

    # Apply any overridden settings
    if override_settings:
        django_settings.update(override_settings)

    # Initialize Django
    django_conf.settings.configure(**django_settings)
    django.setup()
