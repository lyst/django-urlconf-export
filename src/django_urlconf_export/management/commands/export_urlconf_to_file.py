import json

from django.core.management.base import BaseCommand

from django_urlconf_export import export_urlconf


class Command(BaseCommand):
    """
    NOTE: printing output to stdout rather than seeing to a file because this works better with filesystem permissions
    particularly on Linux and/or when using docker

    Examples:

        django-admin export_urlconf_to_file > urlconf.json

        django-admin export_urlconf_to_file \
        --urlconf 'path.to.urlconf' \
        --whitelist 'url-1' 'url-2' 'url-3' \
        --blacklist 'url-4' 'url-5' \
        --language-without-country \
        > urlconf.json

    """

    def add_arguments(self, parser):
        parser.add_argument("--urlconf", type=str, help="Export urls from this urlconf module")
        parser.add_argument(
            "--whitelist", type=str, nargs="*", help="Whitelist urls names and namespaces"
        )
        parser.add_argument(
            "--blacklist", type=str, nargs="*", help="Blacklist urls names and namespaces"
        )
        parser.add_argument(
            "--language-without-country",
            dest="language_without_country",
            action="store_true",
            help="Save multi-language url patterns by language without country",
        )
        parser.add_argument(
            "--include-country",
            dest="language_without_country",
            action="store_false",
            help="Save multi-language url patterns by language + country",
        )
        parser.set_defaults(
            urlconf=None, whitelist=None, blacklist=None, language_without_country=None
        )

    def handle(self, *args, **options):
        print(
            json.dumps(
                export_urlconf.as_json(
                    options["urlconf"],
                    options["whitelist"],
                    options["blacklist"],
                    options["language_without_country"],
                )
            )
        )
