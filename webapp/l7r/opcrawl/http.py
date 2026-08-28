"""The HTTP boundary: one GET, no automatic redirect following, a descriptive User-Agent.

Redirects are returned rather than followed so the census throttles EVERY request - the
redirect hop from a campaign root to the gate page counts against `Crawl-delay` like any other.
The optional cookie is the bare `human_check=` the gate's own JavaScript sets for exempt
campaigns; it is sent only to campaigns on the exempt list.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = 'gm-assistant-research/0.1 (+https://github.com/EliAndrewC/gm-assistant)'


@dataclass(frozen=True)
class Response:
    status: int
    location: str | None
    text: str


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def http_get(url: str, cookie: str | None = None) -> Response:
    headers = {'User-Agent': USER_AGENT}
    if cookie is not None:
        headers['Cookie'] = cookie
    request = urllib.request.Request(url, headers=headers)
    try:
        with _opener.open(request, timeout=60) as resp:
            return Response(
                resp.status, resp.headers.get('Location'), resp.read().decode('utf-8', 'replace')
            )
    except urllib.error.HTTPError as err:
        body = err.read().decode('utf-8', 'replace')
        return Response(err.code, err.headers.get('Location'), body)
