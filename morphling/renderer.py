# -*- coding: utf-8 -*-
import re


class Renderer(object):
    '''
    the default renderer for parser
    '''
    _escape_pattern = re.compile(r'&(?!#?\w+;)')
    _not_allowed_schemes = ['javascript:', 'vbscript:']

    # HTML tags
    _p = 'p'
    _tr = 'tr'

    def __init__(self, **kwargs):
        self._escape = kwargs.get('escape', True)

    @property
    def p(self):
        '''
        <p>
        '''
        return self._p

    @property
    def close_p(self):
        return '</%s>' % self._p

    @property
    def placeholder(self):
        return ''

    @property
    def hr(self):
        return '<hr>\n'

    @property
    def line_break(self):
        return '<br>\n'

    def escape(self, content, quote=False, smart_amp=True):
        if smart_amp:
            content = self._escape_pattern.sub('&amp;', content)
        else:
            content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;').replace('>', '&gt;')
        if quote:
            content = content.replace('"', '&quot;').replace("'", '&#39;')
        return content

    def escape_link(self, link):
        lower_url = link.lower().strip('\x00\x1a \n\r\t')
        for scheme in self._not_allowed_schemes:
            if lower_url.startswith(scheme):
                return ''
        return self.escape(link, quote=True, smart_amp=False)

    def open_tag(self, tag, **kwargs):
        extras = ['%s=%s' % (k, v) for k, v in kwargs.items() if v]
        tag = getattr(self, ''.join(['_', tag]), tag)
        return '<{tag} {attrs}>'.format(tag=tag, attrs=' '.join(extras))

    def close_tag(self, tag, breakline=False):
        tag = getattr(self, ''.join(['_', tag]), tag)
        if breakline:
            return '</%s>\n' % tag
        return '</%s>' % tag

    def block_html(self, tag, content, breakline=True, **kwargs):
        fmt = '{open_t}{cnt}{close_t}'
        return fmt.format(
            open_t=self.open_tag(tag, **kwargs),
            cnt=content,
            close_t=self.close_tag(tag, breakline=breakline)
        )

    def tr(self, content, **kwargs):
        return self.block_html('tr', content, **kwargs)

    def table(self, header, body):
        return (
            '<table>\n<thead>%s</thead>\n'
            '<tbody>\n%s</tbody>\n</table>\n'
        ) % (header, body)

    def code(self, content):
        return self.block_html('code', content, False)

    def emphasis(self, content):
        return self.block_html('em', content, False)

    def double_emphasis(self, content):
        return self.block_html('strong', content, False)

    def strikethrough(self, content):
        return self.block_html('del', content, False)

    def footnote_ref(self, ref_key, index):
        hyperlink = self.block_html(
            'a', index, breakline=False, **{'class': 'footnote', 'href': '#fn:%s' % ref_key})
        return self.block_html('sup', hyperlink, False)
        # return '<sup><a class=footnote href=#fn:%s>%s</a></sup>' % (ref_key, index)

    def link(self, addr, text):
        return self.block_html('a', text, breakline=False, href=addr)
        # return '<a href={addr}>{text}<a>'.format(addr=addr, text=text)

    def img(self, src, alt=None, title=None):
        seg = '<img src=%s' % (self.escape_link(src) if self._escape else src)
        if alt:
            seg += 'alt=%s' % (self.escape(alt) if self._escape else alt)
        if title:
            seg += 'title=%s' % (self.escape(title) if self._escape else title)
        return seg + '>'

    def fence(self, code, language=None, escape=True):
        if escape:
            code = self.escape(code, quote=True, smart_amp=False)
        lang = 'class=lang-%s' % language if language else ''
        return '<pre><code {cls}>{code}\n</code></pre>'.format(cls=lang, code=code)

    def link_definition(self, key, link, **kwargs):
        fmt = '{open_p}[{key}] : {link}{close_p}'
        return fmt.format(open_p=self.open_tag(self.p, **kwargs),
                          key=key, link=link, close_p=self.close_tag(self.p))
