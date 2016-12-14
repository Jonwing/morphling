# coding: utf-8

import re

_escape_pattern = re.compile(r'&(?!#?\w+;)')
_newline_pattern = re.compile(r'\r\n|\r')
_scheme_blacklist = ('javascript:', 'vbscript:')


def escape(text, quote=False, smart_amp=True):
    if smart_amp:
        text = _escape_pattern.sub('&amp;', text)
    else:
        text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    if quote:
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
    return text


def escape_link(url):
    '''
    block the dangerous schemes like javascript, vbscript
    '''
    lower_url = url.lower().strip('\x00\x1a \n\r\t')
    for scheme in _scheme_blacklist:
        if lower_url.startswith(scheme):
            return ''
    return escape(url, quote=True, smart_amp=False)


def preprocessing(text, tab=4):
    text = _newline_pattern.sub('\n', text)
    text = text.expandtabs(tab)
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u2424', '\n')
    pattern = re.compile(r'^ +$', re.M)
    return pattern.sub('', text)
