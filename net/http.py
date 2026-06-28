from curl_cffi.requests import AsyncSession

IMPERSONATE_CHOICES = ("safari260_ios", "chrome131_android")
DEFAULT_IMPERSONATE = "safari260_ios"


def new_async_session(impersonate: str = DEFAULT_IMPERSONATE,
                      headers: dict | None = None,
                      proxy: str | None = None) -> AsyncSession:
    if impersonate not in IMPERSONATE_CHOICES:
        impersonate = DEFAULT_IMPERSONATE
    kw = {"impersonate": impersonate, "headers": headers or {}}
    if proxy:
        kw["proxy"] = proxy
    return AsyncSession(**kw)
