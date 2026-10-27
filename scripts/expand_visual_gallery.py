"""Compatibility helper for the earlier gallery generator.

The current article is built directly by public_gallery. Keeping this function
as an identity prevents older callers from appending repeated video sections.
"""


def expand(text):
    return text
