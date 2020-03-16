import re
from textwrap import dedent

from django.conf import settings
from django.urls import LocalePrefixPattern, URLPattern, URLResolver, get_resolver
from django.urls.resolvers import RegexPattern, RoutePattern
from django.utils import translation
from django.utils.functional import Promise


def assert_url_kwargs_are_the_same_for_all_languages(urlconf=None):
    """
    Call this method in a unit test to check for translation errors in your localised URLs.
    There is a different regex for each language a url is translated into.
    This method asserts each URL has the same kwargs in all supported languages.
    """

    urls = get_resolver(urlconf)

    urls_with_translation_errors = []

    def if_not_none(value):
        if value:
            return value
        return ""

    def find_urls_with_translation_errors(urls, parent_pattern=None):
        for url in urls.url_patterns:
            if isinstance(url, URLResolver):
                find_urls_with_translation_errors(
                    url, if_not_none(parent_pattern) + url.pattern.regex.pattern
                )
            elif isinstance(url, URLPattern):
                full_pattern = if_not_none(parent_pattern) + url.pattern.regex.pattern

                # Ignore Django Admin urls
                if full_pattern.startswith("^admin/"):
                    continue

                # Ignore locale prefix pattern urls
                if isinstance(url.pattern, LocalePrefixPattern):
                    continue

                if isinstance(url.pattern, RegexPattern):
                    pattern_regex = url.pattern._regex
                elif isinstance(url.pattern, RoutePattern):
                    pattern_regex = url.pattern._route
                else:
                    raise ValueError(f"Invalid URL Pattern type: {url.pattern}")

                # We only want to check translated URLs.
                # These will have a promise for their pattern regex.
                if not isinstance(pattern_regex, Promise):
                    continue

                # we only want to check URLs that have kwargs
                # i.e. URLs that have named capture groups
                with translation.override("en"):
                    en_regex = re.compile(str(pattern_regex))
                if not en_regex.groups or not en_regex.groupindex.keys():
                    continue

                # What are the 'en' kwargs?
                en_kwargs = set(en_regex.groupindex.keys())

                # Check each language has the same kwargs
                for language, _ in settings.LANGUAGES:
                    with translation.override(language):
                        language_regex = re.compile(str(pattern_regex))
                        kwargs_for_language = set(language_regex.groupindex.keys())
                    if kwargs_for_language != en_kwargs:
                        urls_with_translation_errors.append(
                            (url.name, full_pattern, language, en_kwargs, kwargs_for_language)
                        )

    find_urls_with_translation_errors(urls)

    error_message = dedent(
        """\
    Found some urls that have not been translated correctly.
    URL keyword arguments should be the same for all languages.
    Here are the errors:

    """
    )

    for name, pattern, language, expected_kwargs, actual_kwargs in urls_with_translation_errors:
        error_message += dedent(
            f"""\
        URL NAME: {name}
        URL PATTERN: {pattern}
        LANGUAGE: {language}
        EXPECTED KWARGS: {", ".join(expected_kwargs)}
        ACTUAL KWARGS: {", ".join(actual_kwargs)}

        """
        )
    assert len(urls_with_translation_errors) == 0, error_message


def assert_all_urls_use_kwargs_not_args(urlconf=None):
    """
    Ensure all URL patterns use named kwargs, rather than unnamed args.
    This makes it easier to translate URLs, because we can change the
    order of the named kwargs without breaking the URL patterns.
    """

    urls = get_resolver(urlconf)

    non_admin_urls_with_args = []

    def if_not_none(value):
        if value:
            return value
        return ""

    def find_non_admin_urls_with_args(urls, parent_pattern=None):
        for url in urls.url_patterns:
            regex = url.pattern.regex

            if isinstance(url, URLResolver):
                find_non_admin_urls_with_args(url, if_not_none(parent_pattern) + regex.pattern)
            elif isinstance(url, URLPattern):
                pattern = if_not_none(parent_pattern) + regex.pattern

                # Ignore Django Admin urls
                if pattern.startswith("^admin/"):
                    continue

                # regex.groups = number of capture groups (named or unnamed) in the url
                # regex.groupindex = dictionary of the named captured groups only.
                if regex.groups and regex.groups != len(regex.groupindex.keys()):

                    # There must be some non-named capture groups.
                    # I.E. some url 'args' as opposed to 'kwargs'

                    # Note that this test will also fail for urls like this:
                    # ^shop/^(?P<gender>(mens|womens))/$

                    # On first glance this doesn't have any 'args'.
                    # However, the brackets within the named gender group count as a group.
                    # These brackets are also unnecessary. The URL works fine like this:
                    # # ^shop/^(?P<gender>mens|womens)/$

                    # In rare cases where the regex requires brackets within a named group
                    # to work properly, you can write 'non-capturing' brackets that begins
                    # with '?:' like this:
                    # (?:mens|womens)

                    non_admin_urls_with_args.append((url.name, pattern))

    find_non_admin_urls_with_args(urls)

    error_message = dedent(
        """\
    Found some urls that include unnamed capture groups (AKA 'url args').
    You need to use named capture groups for all urls (AKA 'url kwargs').

    Note: this test will also fail if you have brackets within a named group like this:

    ^shop/^(?P<gender>(mens|womens))/$

    Brackets like this are not needed. This pattern works exactly the same, and passes this test:

    ^shop/^(?P<gender>mens|womens)/$

    In rare cases where the regex requires brackets within a named group to work properly,
    you can write 'non-capturing' brackets that begin with '?:' like this:

    (?:mens|womens)


    These urls need fixing:

    """
    )

    for name, pattern in non_admin_urls_with_args:
        error_message += dedent(
            """\
        NAME: {name}
        PATTERN: {pattern}

        """.format(
                name=name, pattern=pattern
            )
        )

    assert len(non_admin_urls_with_args) == 0, error_message
