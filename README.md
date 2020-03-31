# Django URLconf Export

![Django URLconf Export logo](https://github.com/lyst/django-urlconf-export/raw/master/logos/box-logo.jpg)

Do you need to make URLs for your Django website in another microservice?

This used to be painful; you had to hard-code URL logic in multiple places.

This was messy and fragile, especially when URLs are translated to multiple languages.

But now, Django URLconf Export has solved this problem.

It exports your website URLconf in a JSON format, then imports it to any other Python service.

So you can make URLs for your website from anywhere, with no hassle, no repetition and no debt.

Some example uses:

* Email microservice that sends links to users.
* Sitmaps generation microservice.
* Microservice that buys paid ads for some website pages.

## Video: 7 minute overview

[![Link to short overview on YouTube](https://github.com/lyst/django-urlconf-export/raw/master/logos/video-link-720p.jpg)](https://youtu.be/3-9_6My5EWg)

## Table of contents

- [Django URLconf Export](https://github.com/lyst/django-urlconf-export#django-urlconf-export)
  * [Video: 7 minute overview](https://github.com/lyst/django-urlconf-export#video-7-minute-overview)
- [User Guide](https://github.com/lyst/django-urlconf-export#user-guide)
  * [Installation](https://github.com/lyst/django-urlconf-export#installation)
  * [Export URLconf as JSON](https://github.com/lyst/django-urlconf-export#export-urlconf-as-json)
  * [Save URLconf to a file](https://github.com/lyst/django-urlconf-export#save-urlconf-to-a-file)
    + [Example use-case](https://github.com/lyst/django-urlconf-export#example-use-case)
  * [Serve URLconf from an endpoint](https://github.com/lyst/django-urlconf-export#serve-urlconf-from-an-endpoint)
    + [Example use-case](https://github.com/lyst/django-urlconf-export#example-use-case-1)
- [Integration](https://github.com/lyst/django-urlconf-export#integration)
  * [Exporting from a Django service](https://github.com/lyst/django-urlconf-export#exporting-from-a-django-service)
  * [Importing in a non-Django service](https://github.com/lyst/django-urlconf-export#importing-in-a-non-django-service)
    + [Edge cases](https://github.com/lyst/django-urlconf-export#edge-cases)
  * [Importing in a Django service with own URLs](https://github.com/lyst/django-urlconf-export#importing-in-a-django-service-with-own-urls)
  * [Importing in a Django service with no URLs](https://github.com/lyst/django-urlconf-export#importing-in-a-django-service-with-no-urls)
- [Feature Details](https://github.com/lyst/django-urlconf-export#feature-details)
  * [Export whitelist and blacklist](https://github.com/lyst/django-urlconf-export#export-whitelist-and-blacklist)
  * [Included URLs](https://github.com/lyst/django-urlconf-export#included-urls)
  * [I18n URLs](https://github.com/lyst/django-urlconf-export#i18n-urls)
  * [Export non-default root URLconf](https://github.com/lyst/django-urlconf-export#export-non-default-root-urlconf)
  * [Quality assurance for i18n URLs](https://github.com/lyst/django-urlconf-export#quality-assurance-for-i18n-urls)
    + [Check for translation errors in URL patterns](https://github.com/lyst/django-urlconf-export#check-for-translation-errors-in-url-patterns)
    + [Ensure URL patterns use kwargs, not args](https://github.com/lyst/django-urlconf-export#ensure-url-patterns-use-kwargs-not-args)
- [Development Guide](https://github.com/lyst/django-urlconf-export#development-guide)
  * [Running tests](https://github.com/lyst/django-urlconf-export#running-tests)
  * [Developing](https://github.com/lyst/django-urlconf-export#developing)
  * [Changing test dependencies](https://github.com/lyst/django-urlconf-export#changing-test-dependencies)
  * [Formatting imports and code](https://github.com/lyst/django-urlconf-export#formatting-imports-and-code)
  * [Publishing to PyPi](https://github.com/lyst/django-urlconf-export#publishing-to-pypi)
- [Further Development](https://github.com/lyst/django-urlconf-export#further-development)

# User Guide

## Installation

The package is called `django-urlconf-export`

Some ways to install:

```shell
pipenv install django-urlconf-export

pip install django-urlconf-export

poetry add django-urlconf-export
```

## Export URLconf as JSON

If you have this URLconf:

```Python
urlpatterns = [
    url(r"^login/$", View.as_view(), name="login"),
]
```

You can run this code:

```Python
from django_urlconf_export import export_urlconf

export_urlconf.as_json()
```

You will get this JSON:

```Python
[
    {"regex": "^login/$", "name": "login"},
]
```

Then somewhere else, you can import the JSON like this:

```Python
from django_urlconf_export import import_urlconf

import_urlconf.from_json(json_urlpatterns)
```

Then you can call `reverse` to make urls, just like normal:

```Python
reverse("login") == "/login/"
```


## Save URLconf to a file

If you add `django_urlconf_export` to your website's `INSTALLED_APPS` you can run:

```shell
django-admin export_urlconf_to_file > "urlconf.json"
```

To create a file called `urlconf.json`

Then you can import the file somewhere else like this:

```python
import_urlconf.from_file("urlconf.json")
```

### Example use-case

At Lyst, we have a skeleton repo that we share with digital agencies who create special pages for us like [The Year in Fashion](https://www.lyst.com/year-in-fashion-2019/). The repo is a stripped-down simulation of our production environment. Agencies develop pages for our website within the repo, so integration is easy.

We include a URLconf file in the skeleton repo. Before we did this, agencies used to hard-code URLs into their work. But now:

* They can make URLs in the standard Django way.
* The URLs are always correct; no silent errors.
* The URLs are localised for all the languages we support.

## Serve URLconf from an endpoint

This view returns URLconf JSON:

```Python
from django_urlconf_export.views.export import URLConfExportView

urlpatterns = [
    url(r"^urlconf/", URLConfExportView.as_view()),
]
```

Then you can import from a URI like this:

```Python
import_urlconf.from_uri("/urlconf/")
```

### Example use-case

A Lyst we have 3 services that make Lyst website urls:

* An email service.
* A sitemaps generation service.
* A paid advertising purchasing service.

These services fetch URLconf from the Lyst website when they boot up, and update it periodically.

So when the URLs change, we don't need to update any service code. This is particularly helpful when we add a new language for our localised URLs.

# Integration

## Exporting from a Django service

In most situations, the best approach is to [serve URLconf from an endpoint](https://github.com/lyst/django-urlconf-export#serve-urlconf-from-an-endpoint).

In some situations, it might work better if you [save URLconf to a file](https://github.com/lyst/django-urlconf-export#save-urlconf-to-a-file).

If you have a specialised use-case that isn't handled by either of these approaches, You could roll your own core logic to [export URLconf as JSON](https://github.com/lyst/django-urlconf-export#export-urlconf-as-json).

If you roll a bespoke integration you think might be useful to others, please feel free to submit a PR.

## Importing in a non-Django service

You can import URLconf and make URLs in any Python code.

First, add Django as a dependency e.g. `pip install django`

Then call `import_urlconf.init_django()` before you import any URLconf e.g.

```python
from django_urlconf_export import import_urlconf

import_urlconf.init_django()

import_urlconf.from_uri("https://www.example.com/urlconf/")
```

Then you can call `reverse()` and make URLs for your website, just like in the website code.

### Edge cases

By default, Django will be initialized with `settings.ROOT_URLCONF == "imported_urlconf"`

The module will be created when you import some urlconf.

If you need to set `settings.ROOT_URLCONF` to different module name, you can:

```python
import_urlconf.init_django(ROOT_URLCONF="another_urlconf_module")
```

You can set any other Django settings this way too. 

See [the source code](https://github.com/lyst/django-urlconf-export/blob/master/src/django_urlconf_export/import_urlconf.py) for the default Django settings.


## Importing in a Django service with own URLs

By default, the library imports URLconf into the root URLconf module of the service - `settings.ROOT_URLCONF`. 

But if the service has its own URLs, `settings.ROOT_URLCONF` will have some URLconf in it already.

To avoid overwriting the service's URLs, you can import to a different module with this Django setting:

```python
URLCONF_IMPORT_ROOT_URLCONF = "imported_urlconf"
```

Or you can add a `urlconf="..."` argument when you import:

```python
import_urlconf.from_file("urlconf.json", urlconf="imported_urlconf")
```

If the module does not exist, it will be created - so you can call it anything you like.

If the module exists, any existing `urlpatterns` will be overwritten.

Then you can make a url like:

```python
reverse("login", urlconf="imported_urlconf")
```

Or for convenience, you could make a `website_urls.py` module like this:

```python
from django import urls as django_urls
from django.apps import AppConfig
from django_urlconf_export import import_urlconf


class WebsiteURLsAppConfig(AppConfig):
    name = "website_urls"
    verbose_name = "Make URLs for our website in any Django service."

    def ready(self):
        """
        When Django initializes, get the latest urlconf from our website.
        """
        update_urlconf()


def update_urlconf():
    """
    Download the latest urlconf from our website
    """
    import_urlconf.from_uri("https://www.example.com/urlconf/", urlconf="imported_urlconf")


def reverse(*args, **kwargs):
    """
    Thin wrapper for Django's reverse method, to make a URL for our website.
    """
    return django_urls.reverse(*args, urlconf="imported_urlconf", **kwargs)
```

Adding `"website_urls.WebsiteURLsAppConfig"` to `INSTALLED_APPS` in Django setting will import the URLconf when Django starts up.

Then you can make URLs for your website by calling `website_urls.reverse(...)`

If you want to update the URLconf later, you can call `website_urls.update_urlconf()`.

## Importing in a Django service with no URLs

If your Django service doesn't have any URLs of it's own, you can store imported URLconf in the default URLconf module - `settings.ROOT_URLCONF`.

This makes things a bit simpler. You could make a `website_urls.py` module like this:

```python
from django.apps import AppConfig
from django_urlconf_export import import_urlconf


class WebsiteURLsAppConfig(AppConfig):
    name = "website_urls"
    verbose_name = "Make URLs for our website in any Django service."

    def ready(self):
        """
        When Django initializes, get the latest urlconf from our website.
        """
        update_urlconf()


def update_urlconf():
    """
    Download the latest urlconf from our website
    """
    import_urlconf.from_uri("https://www.example.com/urlconf/")
```

Adding `"website_urls.WebsiteURLsAppConfig"` to `INSTALLED_APPS` in Django setting will import the URLconf when Django starts up.

Then you can call `reverse()` and make URLs for your website, just like in the website code:

```python
from django.urls import reverse

reverse(...)
```

If you want to update the URLconf later, you can call `website_urls.update_urlconf()`.

# Feature Details

If you prefer to read code than docs, the tests have examples of all feature details:

* [export_urlconf tests](https://github.com/lyst/django-urlconf-export/blob/master/tests/django_urlconf_export/test_export_urlconf.py)
* [import_urlconf tests](https://github.com/lyst/django-urlconf-export/blob/master/tests/django_urlconf_export/test_import_urlconf.py)

## Export whitelist and blacklist

By default, all URLs will be exported. But you can set a whitelist and/or blacklist with these Django settings:

```python
URLCONF_EXPORT_WHITELIST = {"only-show-this-url"}
URLCONF_EXPORT_BLACKLIST = {"hide-this-url", "hide-this-one-too"}
```

The whitelist is applied first, then the blacklist.

List items can be regexes, for example `"secret-."` matches all URL names that start with `secret-` like `secret-page-1`, `secret-page-2` etc.

The whitelist and blacklist sets are a mixture of:

* URL names
* URL namespaces

For included URLs with a `namespace` (see [Django docs](https://docs.djangoproject.com/en/3.0/topics/http/urls/#url-namespaces)) like the Django admin urls, the `namespace` and the `url_name` must be _both_ be allowed by the lists. 

So you can ban all URLs in the `admin` namespace with `blacklist = {"admin"}`.

If you want to export `admin:some-url` but no other `admin` URLs, set `whitelist = {"admin", "some-url"}`. 

Note: if you set `whitelist = {"admin"}` _no admin URLs will be exported_.

See the [unit tests](https://github.com/lyst/django-urlconf-export/blob/master/tests/django_urlconf_export/test_export_urlconf.py) for more examples.

You can check the whitelist and/or blacklist are working as expected like this:

```python
print(export_urlconf.get_all_allowed_url_names())
```

You can also set whitelist or blacklist explicitly when exporting as JSON:

```Python
export_urlconf.as_json(
    whitelist={"only-show-this-url"},
    blacklist={"hide-this-url", "hide-this-one-too"}
)
```

Or when generating a file:

```shell
django-admin export_urlconf_to_file \
        --whitelist 'only-show-this-url' \
        --blacklist 'hide-this-url", "hide-this-one-too' \
        > urlconf.json
```

Or when serving from an endpoint:

```Python
urlpatterns = [
    url(r"^urlconf/", URLConfExportView.as_view(
        whitelist={"only-show-this-url"},
        blacklist={"hide-this-url", "hide-this-one-too"}
    )),
]
```

## Included URLs

We fully support included URLconf. The JSON looks like:

```python
{
    "regex": "^colors/",
    "namespace": None,
    "app_name": None,
    "includes": [
        {"regex": "^red/$", "name": "red"},
        {"regex": "^blue/$", "name": "blue"}
    ],
}
```

## I18n URLs

We fully support internationalized URLs. 

The JSON looks like:

```python
{
    "regex": {
        "en-us": "^color/$",
        "en-gb": "^colour/$",
        "fr-fr": "^couleur/$"
    },
    "name": "color"
}
```

---

Some websites (e.g. Lyst) only localise URLs at the language-family level.

For example, `en` rather than `en-us` and `en-gb`.

If you set this Django setting:

```python
URLCONF_EXPORT_LANGUAGE_WITHOUT_COUNTRY = True
```

Then you get JSON like:

```python
{
    "regex": {
        "en": "^color/$",
        "fr": "^couleur/$"
    },
    "name": "color"
}
```

You can also add an argument when exporting as JSON:

```Python
export_urlconf.as_json(language_without_country=True)
```

Or when generating a file:

```shell
django-admin export_urlconf_to_file --language-without-country > urlconf.json
```

Or when serving from an endpoint:

```Python
urlpatterns = [
    url(r"^urlconf/", URLConfExportView.as_view(language_without_country=True)),
]
```

---

We support the `LocalePrefixPattern` (see [Django docs](https://docs.djangoproject.com/en/3.0/topics/i18n/translation/#language-prefix-in-url-patterns).

So if you have URLconf like:

```python
from django.conf.urls.i18n import i18n_patterns

urlpatterns = i18n_patterns(
    url(r"^$", View.as_view(), name="index"),
)
```

You get JSON like:

```python
{
    "isLocalePrefix": True,
    "classPath": "django.urls.resolvers.LocalePrefixPattern",
    "includes": [
        {"regex": "^$", "name": "index"}
    ],
}
```

Note that `classPath` is saved in the JSON. So if (like Lyst) your project uses a subclass of Django's `LocalePrefixPattern` it will work.

## Export non-default root URLconf

By default, we export the root URLconf module that creates the endpoints of your Django website: `settings.ROOT_URLCONF`. This is almost always what you want.

If you need to export from a different root URLconf module, you can use this Django setting:

```python
URLCONF_EXPORT_ROOT_URLCONF = "path.to.non_default_root_urlconf"
```

Or when exporting as JSON:

```Python
export_urlconf.as_json("path.to.non_default_root_urlconf")
```

Or when generating a file:

```shell
django-admin export_urlconf_to_file \
        --urlconf 'path.to.non_default_root_urlconf' \
        > urlconf.json
```

Or when serving from an endpoint:

```Python
urlpatterns = [
    url(r"^urlconf/", URLConfExportView.as_view(
        urlconf="path.to.non_default_root_urlconf",
    )),
]
```

## Quality assurance for i18n URLs

This library is particularly useful if you have internationalized URLs.

We provide some methods to help ensure URLs are translated correctly.

### Check for translation errors in URL patterns

If you want to check that URL pattern kwargs are the same for all translations of a URL, you can add a unit test to your project like:

```python
from django_urlconf_export import urlconf_qa

def test_for_url_translation_errors():
    urlconf_qa.assert_url_kwargs_are_the_same_for_all_languages()
```

### Ensure URL patterns use kwargs, not args

Django allows you to make URL patterns that have positional arguments (`args`) and/or named keyword arguments (`kwargs`).

This flexibility can lead to confusion, particularly in large teams. So it can be helpful to ensure developers only use `kwargs` and not `args`.

It's also less error-prone to translate URLs that use `kwargs`, because translators are free to change the order of `kwargs` in the URL to match the word order in their language.

For example, at Lyst we have URLs like:

|         | Example URL   | Localised URL Pattern                         |
|---------|---------------|-----------------------------------------------|
| English | `/gucci-bags` | `/(?P<designer_name>.+)-(?P<product_type>.+)` |
| French  | `/sacs-gucci` | `/(?P<product_type>.+)-(?P<designer_name>.+)` |

To enforce that URL patterns always use `kwargs` and not `args`, add a test like this:

```python
from django_urlconf_export import urlconf_qa

def test_all_urls_use_kwargs():
    urlconf_qa.assert_all_urls_use_kwargs_not_args()
```

# Development Guide

## Running tests

`pip install tox` (or `pip3 install tox`)
 
Then run `tox`

## Developing

`pip install --user pipenv` (or `pip3 install --user pipenv`)

Then run:
 
* `pipenv install`
* `pipenv shell`
* `exit`
* `pipenv --venv`

The location of the virtual environment will be displayed.

Here is a [guide for using this venv in PyCharm](https://stackoverflow.com/a/50749980/3048733).

## Changing test dependencies

You need to `pipenv install {new-dependency}` and also add the dependency in `tox.ini`.

## Formatting imports and code

First run `pipenv shell`

Then run:

* `isort` - format imports
* `black src/ tests/` - format code

Then `exit` to quit the shell.

## Publishing to PyPi

Create a new release, and the package will be published automatically by a GitHub action. 

# Further Development

It would be cool if we could make URLs in JavaScript using the JSON generated by this library. Then we could make URLs on the front-end, and in Node services.

Lyst are not working on this at the moment. If this feature would be useful to you, a PR would be very welcome :)
