from markupsafe import Markup
from werkzeug.urls import url_parse

from lektor.constants import PRIMARY_ALT
from lektor.context import get_ctx
from warnings import warn

# + patch
from bs4 import BeautifulSoup
from lektor.markdown import Markdown
from lektor.types.base import Type
# - patch


class MarkdownDescriptor:
    def __init__(self, source, options):
        self.source = source
        self.options = options

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return Markdown(self.source, record=obj, field_options=self.options)


class MarkdownType(Type):
    widget = "multiline-text"

    def __init__(self, env, options):
        super().__init__(env, options)
        _check_option(options, "resolve_links", ("always", "never", "when-possible"))

    def value_from_raw(self, raw):
        return MarkdownDescriptor(raw.value or "", self.options)


def _check_option(options, name, choices):
    value = options.get(name)
    if value is not None and value not in choices:
        message = (
            f"Unrecognized value {value!r} for the {name!r} markdown field option. "
            f"Valid values are: {', '.join(repr(_) for _ in choices)}."
        )
        warn(message, stacklevel=3)


# + patch
# Wrapper with an __html__ method prevents Lektor from escaping HTML tags.
class HTML:
    def __init__(self, html):
        self.html = html

    def __html__(self):
        return self.html


class HTMLDescriptor:
    def __init__(self, source, options):
        self.source = source
        self.options

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        base_url = get_ctx().base_url

        soup = BeautifulSoup(self.source, features="html.parser")
        for img in soup.find_all("img"):
            src = img["src"]
            url = url_parse(src)
            if not url.scheme:
                img["src"] = obj.url_to(src, alt=PRIMARY_ALT, base_url=base_url)
        for link in soup.find_all("a"):
            href = link["href"]
            url = url_parse(href)
            if not url.scheme:
                link["href"] = obj.url_to(href, alt=PRIMARY_ALT, base_url=base_url)
        return Markup(str(soup))


class HtmlType(Type):
    widget = "multiline-text"

    def value_from_raw(self, raw):
        if raw.value is None:
            return raw.missing_value("Missing HTML")
        return HTMLDescriptor(raw.value or u"", self.options)

# - patch