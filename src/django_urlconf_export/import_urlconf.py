import json
import sys
import types
from pydoc import locate

import requests
from django.conf import settings
from django.urls import LocalePrefixPattern, URLPattern, URLResolver
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


def _add_django_urlpatterns_to_module(django_urlpatterns, urlconf):
    """
    Add Django URLconf to a module. Create the module if necessary.

    :param django_urlpatterns: list of Django URLResolver and URLPattern objects
    :param urlconf: string - name of module to save the urlpatterns in
    :return: None
    """
    urlconf = urlconf or getattr(settings, "ROOT_URLCONF", None)
    if not urlconf:
        raise ValueError(
            "Urlconf is not defined. You must set settings.ROOT_URLCONF "
            "or specify a urlconf module name when importing urls. "
            "You can use any name you like for the urlconf module, and "
            "it will be created if it doesn't already exist."
        )

    if sys.modules.get(urlconf):
        # Load existing module
        urlconf_module = sys.modules.get(urlconf)
    else:
        # Create module
        urlconf_module = types.ModuleType(urlconf, "Imported URLs will live in this module")
        sys.modules[urlconf] = urlconf_module

    if hasattr(urlconf_module, "urlpatterns"):
        # Add to existing urlpatterns
        urlconf_module.urlpatterns += django_urlpatterns
    else:
        # Create urlpatterns
        urlconf_module.urlpatterns = django_urlpatterns


def from_json(json_urlpatterns, urlconf=None):
    """
    Import URLconf from a list of JSON dict

    :param json_urlpatterns: list of JSON URLconf dicts
    :param urlconf: string - name of module to import URLconf into
    :return: None
    """
    django_urlpatterns = _get_django_urlpatterns(json_urlpatterns)
    _add_django_urlpatterns_to_module(django_urlpatterns, urlconf)


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
