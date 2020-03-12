import re

from django import urls as django_urls
from django.conf import settings
from django.urls import LocalePrefixPattern, URLPattern, URLResolver
from django.urls.resolvers import RegexPattern, RoutePattern
from django.utils import translation
from django.utils.functional import Promise

from django_urlconf_export import language_utils


def _get_url_languages(language_without_country):
    """
    Some websites only translate urls once for each language family e.g. "en",
    not each language + country combination e.g. "en-gb" and "en-us".

    :param language_without_country: boolean
        Should translated URLs be keyed by e.g. "en" rather than "en-gb" and "en-us"?
    :return: language code e.g. "en" or "en-us"
    """
    if language_without_country:
        return {language_utils.get_without_country(language) for language, _ in settings.LANGUAGES}
    else:
        return {language for language, _ in settings.LANGUAGES}


def _get_regex_pattern(url_pattern, language_without_country):
    """
    Export data from a Django URLPattern as JSON

    :param url_pattern: URLPattern
    :param language_without_country:
    :return: tuple(string, string or None)
        pattern_type - 'route', 'regex' or 'prefix'
        pattern_regex - string or None
    """
    if isinstance(url_pattern, LocalePrefixPattern):
        return "prefix", None
    elif isinstance(url_pattern, RegexPattern):
        pattern_type = "regex"
        pattern_regex = url_pattern._regex
    elif isinstance(url_pattern, RoutePattern):
        pattern_type = "route"
        pattern_regex = url_pattern._route
    else:
        raise ValueError(f"Invalid URL Pattern type: {url_pattern}")

    if isinstance(pattern_regex, Promise):
        language_regexes = {}
        for lang in _get_url_languages(language_without_country):
            with translation.override(lang):
                language_regexes[lang] = str(pattern_regex)
        return pattern_type, language_regexes
    else:
        return pattern_type, pattern_regex


def _is_allowed(name, whitelist, blacklist):
    """
    Check if this url (or url namespace) is allowed to be exported.

    :param name: url name OR included urls namespace
    :param whitelist: list of strings; url_names and namespaces, allowed to be exported.
    :param blacklist: list of strings; url_names and namespaces, not allowed to be exported.
    :return: boolean - is this url or namespace allowed to be exported?
    """
    if not whitelist and not blacklist:
        return True

    if blacklist and not whitelist:
        return not any(re.match(pattern, name) for pattern in blacklist)

    if whitelist and not blacklist:
        return any(re.match(pattern, name) for pattern in whitelist)

    if whitelist and blacklist:
        for whitelisted_pattern in whitelist:
            if re.match(whitelisted_pattern, name):
                # It's whitelisted. Check it's not blacklisted.
                if not any(
                    re.match(blacklisted_pattern, name) for blacklisted_pattern in blacklist
                ):
                    return True
        return False


def _get_json_urlpatterns(resolver, whitelist=None, blacklist=None, language_without_country=False):
    """
    Export URLconf data from a Django URLResolver, as list of JSON dictionaries

    :param resolver: URLResolver - resolver to export URLconf data from
    :param whitelist: list of strings; url_names and namespaces, allowed to be exported.
    :param blacklist: list of strings; url_names and namespaces, not allowed to be exported.
    :param language_without_country: boolean
        Should translated URLs be keyed by e.g. "en" rather than "en-gb" and "en-us"?
    :return: list of JSON URLconf dicts
    """
    json_urlpatterns = []
    for django_url in resolver.url_patterns:
        json_url = {}

        # Example values:
        # pattern_type | pattern_regex
        # ----------------------------
        # 'route'      | '/home/'
        # 'regex'      | '^/home/$'
        # 'prefix'     | None
        pattern_type, pattern_regex = _get_regex_pattern(
            django_url.pattern, language_without_country
        )
        if pattern_type in ["route", "regex"]:
            json_url[pattern_type] = pattern_regex

        if isinstance(django_url, URLResolver):
            includes = _get_json_urlpatterns(
                django_url, whitelist, blacklist, language_without_country
            )
            # If no live urls are included,
            # skip this URLResolver in the json
            if not includes:
                continue
            json_url["includes"] = includes
            if isinstance(django_url.pattern, LocalePrefixPattern):
                json_url["isLocalePrefix"] = True
                # classPath = "package.subpackage.ClassName"
                json_url["classPath"] = ".".join(
                    [
                        django_url.pattern.__class__.__module__,
                        django_url.pattern.__class__.__qualname__,
                    ]
                )
            else:
                # If a namespace is set, check it is allowed
                if django_url.namespace and not _is_allowed(
                    django_url.namespace, whitelist, blacklist
                ):
                    continue
                json_url["app_name"] = django_url.app_name
                json_url["namespace"] = django_url.namespace

        elif isinstance(django_url, URLPattern):
            # Ignore urls without a name,
            # they are typically dead or redirecting.
            # Without a name, we cannot reverse the django_url anyway.
            if not django_url.name:
                continue
            # Check this url name is allowed
            if not _is_allowed(django_url.name, whitelist, blacklist):
                continue
            json_url["name"] = django_url.name

        json_urlpatterns.append(json_url)
    return json_urlpatterns


def as_json(urlconf=None, whitelist=None, blacklist=None, language_without_country=None):
    """
    Export URLconf data from a module, as list of JSON dictionaries.

    :param urlconf: string - root module name to export URLconf from
    :param whitelist: list of strings; url_names and namespaces, allowed to be exported.
    :param blacklist: list of strings; url_names and namespaces, not allowed to be exported.
    :param language_without_country: boolean
        Should translated URLs be keyed by e.g. "en" rather than "en-gb" and "en-us"?
    :return: list of JSON URLconf dicts
    """

    if urlconf is None:
        urlconf = getattr(settings, "URLCONF_EXPORT_ROOT_URLCONF", settings.ROOT_URLCONF)

    if whitelist is None:
        whitelist = getattr(settings, "URLCONF_EXPORT_WHITELIST", None)

    if blacklist is None:
        blacklist = getattr(settings, "URLCONF_EXPORT_BLACKLIST", None)

    if language_without_country is None:
        language_without_country = getattr(
            settings, "URLCONF_EXPORT_LANGUAGE_WITHOUT_COUNTRY", False
        )

    root_resolver = django_urls.get_resolver(urlconf)

    return _get_json_urlpatterns(root_resolver, whitelist, blacklist, language_without_country)


def get_all_exported_url_names(json_urlpatterns):
    """
    Get all names and namespaces in some URLconf JSON.

    :param json_urlpatterns: list of JSON URLconf dicts
    :return: list of strings; url_names and namespaces
    """
    url_names = set()
    for url in json_urlpatterns:
        included_urls = url.get("includes")
        if included_urls:
            if url["namespace"] is not None:
                url_names.add(url["namespace"])
            url_names |= get_all_exported_url_names(included_urls)
        else:
            url_names.add(url["name"])
    return url_names


def get_all_allowed_url_names(
    urlconf=None, whitelist=None, blacklist=None, language_without_country=None
):
    """
    Useful to check whitelist and blacklist are working as expected

    :param urlconf: string - root module name to export URLconf from
    :param whitelist: list of strings; url_names and namespaces, allowed to be exported.
    :param blacklist: list of strings; url_names and namespaces, not allowed to be exported.
    :param language_without_country: boolean
        Should translated URLs be keyed by e.g. "en" rather than "en-gb" and "en-us"?
    :return: list of strings; url_names and namespaces
    """
    json_urlpatterns = as_json(urlconf, whitelist, blacklist, language_without_country)
    return get_all_exported_url_names(json_urlpatterns)
