import pytest
from django.test import override_settings

from django_urlconf_export import import_urlconf, urlconf_qa


@override_settings(LANGUAGES=[("en", "English"), ("fr", "French")],)
def test_check_urlpattern_translations_will_pass(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                "regex": {
                    # e.g. /gucci-bags/
                    "en": "^(?P<designer_name>.+)-(?P<product_type>.+)/$",
                    # e.g. /sacs-gucci/
                    "fr": "^(?P<product_type>.+)-(?P<designer_name>.+)/$",
                },
                "name": "designer-products",
            }
        ],
        urlconf="mock_urlconf_module",
    )
    # kwargs are same for both languages, so this will not error
    urlconf_qa.assert_url_kwargs_are_the_same_for_all_languages("mock_urlconf_module")


@override_settings(LANGUAGES=[("en", "English"), ("fr", "French")],)
def test_check_urlpattern_translations_will_fail(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                "regex": {
                    # e.g. /gucci-bags/
                    "en": "^(?P<designer_name>.+)-(?P<product_type>.+)/$",
                    # ERROR: the kwarg names have been translated by mistake
                    # so they're no longer the same as the English pattern kwargs.
                    "fr": "^(?P<type_de_produit>.+)-(?P<nom_du_créateur>.+)/$",
                },
                "name": "designer-products",
            }
        ],
        urlconf="mock_urlconf_module",
    )
    with pytest.raises(AssertionError):
        urlconf_qa.assert_url_kwargs_are_the_same_for_all_languages("mock_urlconf_module")


def test_urlpatterns_use_kwargs_will_pass(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                # e.g. /gucci-bags/
                "regex": "^(?P<designer_name>.+)-(?P<product_type>.+)/$",
                "name": "designer-products",
            }
        ],
        urlconf="mock_urlconf_module",
    )
    # The url is using kwargs, not args, so this won't error
    urlconf_qa.assert_all_urls_use_kwargs_not_args("mock_urlconf_module")


def test_urlpatterns_use_kwargs_will_fail(mock_urlconf_module):
    import_urlconf.from_json(
        [
            {
                # ERROR: using unnamed args in the pattern
                "regex": "^(.+)-(.+)/$",
                "name": "designer-products",
            }
        ],
        urlconf="mock_urlconf_module",
    )
    with pytest.raises(AssertionError):
        urlconf_qa.assert_all_urls_use_kwargs_not_args("mock_urlconf_module")
