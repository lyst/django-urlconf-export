from django.http import Http404
from django.views import View


class Http404View(View):
    """
    When we import URLconf, we must associate a view with each URL pattern.
    So we use this view that always returns 404.
    """

    def dispatch(self, request, *args, **kwargs):
        raise Http404("not found")
