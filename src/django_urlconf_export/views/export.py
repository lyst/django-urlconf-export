from django.http import JsonResponse
from django.views import View

from django_urlconf_export import export_urlconf


class URLConfExportView(View):
    """
    This view returns URLconf json. Usage example:

    url(r"^urlconf/", URLConfExportView.as_view(blacklist=["secret-url"])),
    """

    urlconf = None
    whitelist = None
    blacklist = None
    language_without_country = None

    def get(self, request):
        exported_urls = export_urlconf.as_json(
            self.urlconf, self.whitelist, self.blacklist, self.language_without_country
        )
        return JsonResponse(exported_urls, safe=False)
