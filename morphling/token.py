# coding: utf-8

import re


_inline_tags = [
    'a', 'em', 'strong', 'small', 's', 'cite', 'q', 'dfn', 'abbr', 'data',
    'time', 'code', 'var', 'samp', 'kbd', 'sub', 'sup', 'i', 'b', 'u', 'mark',
    'ruby', 'rt', 'rp', 'bdi', 'bdo', 'span', 'br', 'wbr', 'ins', 'del',
    'img', 'font',
]
_valid_end = r'(?!:/|[^\w\s@]*@)\b'
_valid_attr = r'''\s*[a-zA-Z\-](?:\=(?:"[^"]*"|'[^']*'|\d+))*'''
_block_tag = r'(?!(?:%s)\b)\w+%s' % ('|'.join(_inline_tags), _valid_end)


class TokenBase(object):
    _blank_regex = re.compile(r'\s+')
    regex = None

    def __init__(self, matchs=None, scanner=None):
        self.matchs = matchs
        self.scanner = scanner
        if not scanner:
            return
        if matchs:
            self.setup()

    def _clone(self):
        obj = self.__class__()
        for k, v in self.__dict__.items():
            obj.__dict__[k] = v
        return obj

    @classmethod
    def add_to_scanner(cls, scanner, match_type='d'):
        '''
        add cls to the regex pool of scanner
        :params scanner: instance of Scanner
        :match_type: which pool to add. 'd': default; 'l': list; 'f':footnote;
        '''
        matchs = {'d': 'default_regex', 'l': 'list_regex', 'f': 'footnote_regex'}
        pool = getattr(scanner, matchs[match_type])
        pool.append(cls)

    @classmethod
    def pattern(cls, only_pattern=True):
        '''
        return the pattern of a token
        :param only_pattern: remove the '^' at the begining of the pattern
        '''
        ptn = cls.regex.pattern
        if only_pattern and ptn.startswith('^'):
            ptn = ptn[1:]
        return ptn

    @property
    def length(self):
        '''
        the length of the matched content
        '''
        if not self.matchs:
            return 0
        return len(self.matchs.group(0))

    @classmethod
    def match(cls, source, scanner=None):
        '''
        try to match the given source with cls's pattern
        :param source: source to match
        :param scanner: instance of a Scanner class
        '''
        match = cls.regex.match(source)
        if not match:
            return None
        new_token = cls(match, scanner=scanner)
        return new_token

    def __repr__(self):
        return '<{0}>'.format(self.__class__.__name__)

    def setup(self):
        '''
        add the token self to scanner's parsed token queue
        '''
        self.scanner.add_token(self)

    def as_html(self, renderer):
        '''
        output token as html
            :params renderer: instance of InlineScanner
        '''
        raise NotImplementedError

    def _shrink_blank_characters(self, s):
        '''
        lower the given string and shrink its blank continuous characters into 1 space
        '''
        return self._blank_regex.sub(' ', s.lower())


class BlockToken(TokenBase):

    def as_html(self, renderer):
        return '[%s to be rendered. content: %s]\n' % (
            self.__class__.__name__, self.matchs.group(0))


class InlineToken(TokenBase):

    def as_html(self, renderer):
        return '[%s to be rendered. content: %s]\n' % (
            self.__class__.__name__, self.matchs.group(0))


class SeperatedToken(TokenBase):
    '''
    for tokens that have seperated open and close tags.
    '''
    def __init__(self):
        # set is_head
        pass


class BlockLink(BlockToken):
    regex = re.compile(
        r'^ *\[([^^\]]+)\]: *'  # [key]:
        r'<?([^\s>]+)>?'  # <link> or link
        r'(?: +["(]([^\n]+)[")])? *(?:\n+|$)'
    )

    def setup(self):
        self._refkey = self._shrink_blank_characters(self.matchs.group(1))
        self.link = self.matchs.group(2)
        self.title = self.matchs.group(3)
        self.scanner.add_link(self)

    def as_html(self, renderer):
        return renderer.link_definition(self.ref_key, self.link)

    @property
    def ref_key(self):
        return self._refkey


class BlockFootnote(BlockToken):
    regex = re.compile(r'(\ ?\ ?\ ?)\[\^([^\]]*)\]:\s*(.*)')

    def setup(self):
        self.is_head = True
        self.key = self._shrink_blank_characters(self.matchs.group(2) or self.matchs.group(1))
        self.description = self.matchs.group(3)
        self.scanner.add_token(self)
        self.scanner.parse(self.description, self.scanner.default_inline_regex)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)
        self.scanner.move_block_to_footnotes(self.__class__)

    def as_html(self, renderer):
        if self.is_head:
            return renderer.open_tag('li', id='fn:%s' % self.key)
        return renderer.close_tag('li')


class NewLine(BlockToken):
    regex = re.compile(r'^\n+')

    def setup(self):
        if self.length > 1:
            self.scanner.add_token(self)

    def as_html(self, renderer):
        return '\n'


class BlockCode(BlockToken):
    regex = re.compile(r'^( {4}[^\n]+\n*)+')
    _leading_pattern = re.compile(r'^ {4}', re.M)

    def setup(self):
        self.content = self._leading_pattern.sub('', self.matchs.group(0))
        super(BlockCode, self).setup()

    def as_html(self, renderer):
        return renderer.fence(self.content.rstrip('\n'))


class Fence(BlockToken):
    regex = re.compile(
        r'^ *(`{3,}|~{3,}) *(\S+)? *\n'  # ```lang
        r'([\s\S]+?)\s*'
        r'\1 *(?:\n+|$)'  # ```
    )

    def setup(self):
        self.language = self.matchs.group(2)
        self.content = self.matchs.group(3)
        super(Fence, self).setup()

    def as_html(self, renderer):
        return renderer.fence(self.content.rstrip('\n'), self.language)


class Hrule(BlockToken):
    regex = re.compile(r'^ {0,3}[-*_](?: *[-*_]){2,} *(?:\n+|$)')

    def as_html(self, renderer):
        return renderer.hr


class Heading(BlockToken):
    regex = re.compile(r'^ *(#{1,6}) *([^\n]+?) *#* *(?:\n+|$)')

    def setup(self):
        self.is_head = True
        self.heading_level = len(self.matchs.group(1))
        self.content = self.matchs.group(2)
        super(Heading, self).setup()
        self.scanner.parse(self.content, self.scanner.default_inline_regex)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)

    def as_html(self, renderer):
        heading = 'h{lvl}'.format(lvl=self.heading_level)
        if self.is_head:
            return renderer.open_tag(heading)
        return renderer.close_tag(heading, True)


class LHeading(Heading):
    regex = re.compile(r'^([^\n]+)\n *(=|-)+ *(?:\n+|$)')

    def setup(self):
        self.is_head = True
        self.heading_level = 1 if self.matchs.group(2) == '=' else 2
        self.content = self.matchs.group(1)
        self.scanner.add_token(self)
        self.scanner.parse(self.content, self.scanner.default_inline_regex)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)


class BlockQuote(BlockToken):
    regex = re.compile(r'^( *>[^\n]+(\n[^\n]+)*\n*)+')
    _leading_pattern = re.compile(r'^ *> ?', re.M)
    is_head = None  # leading mark

    def __init__(self, matchs=None, scanner=None, is_head=None):
        self.is_head = is_head
        super(BlockQuote, self).__init__(matchs, scanner)

    def setup(self):
        self.is_head = True
        super(BlockQuote, self).setup()
        washed = self._leading_pattern.sub('', self.matchs.group(0))
        self.scanner.parse(washed)
        block_end = BlockQuote(scanner=self.scanner, is_head=False)
        self.scanner.add_token(block_end)

    def as_html(self, renderer):
        if self.is_head:
            return renderer.open_tag('blockquote')
        return renderer.close_tag('blockquote', breakline=True)


class ListItem(BlockToken):
    regex = re.compile(
        r'^(( *)(?:[*+-]|\d+\.) [^\n]*'
        r'(?:\n(?!\2(?:[*+-]|\d+\.) )[^\n]*)*)',
        flags=re.M
    )

    def __init__(self, matchs=None, scanner=None, is_head=None):
        self.is_head = is_head
        super(ListItem, self).__init__(matchs, scanner)

    def as_html(self, renderer):
        if self.is_head:
            return renderer.open_tag('li')
        return renderer.close_tag('li', breakline=True)


class ListBullet(BlockToken):
    regex = re.compile(r'^ *(?:[*+-]|\d+\.) +')


class ListBlock(BlockToken):
    regex = re.compile(
        r'^( *)([*+-]|\d+\.) [\s\S]+?'
        r'(?:'
        r'\n+(?=\1?(?:[-*_] *){3,}(?:\n+|$))'
        r'|\n+(?=%s)'
        r'|\n+(?=%s)'
        r'|\n{2,}'
        r'(?! )'
        r'(?!\1(?:[*+-]|\d+\.) )\n*'
        r'|'
        r'\s*$)' % (
            BlockLink.pattern(),
            BlockFootnote.pattern(),
        )
    )
    list_item_token = ListItem
    list_bullet_token = ListBullet
    is_head = None

    def __init__(self, matchs=None, scanner=None, is_head=None, **kwargs):
        self.is_head = is_head
        self.ordered = kwargs.get('ordered')
        super(ListBlock, self).__init__(matchs, scanner)

    def setup(self):
        self.ordered = '.' in self.matchs.group(2)
        self.is_head = True
        self.scanner.add_token(self)

        # parse list items
        items = self.list_item_token.regex.findall(self.matchs.group(0))
        for item, _ in items:
            space = len(item)
            item = self.list_bullet_token.regex.sub('', item)

            if '\n' in item:
                space = space - len(item)
                item = re.compile(r'^ {1,%d}' % space, flags=re.M).sub('', item)

            self.scanner.add_token(
                self.list_item_token(scanner=self.scanner, is_head=True))
            self.scanner.parse(item, self.scanner.list_regex)
            self.scanner.add_token(
                self.list_item_token(scanner=self.scanner, is_head=False))
        list_end = ListBlock(scanner=self.scanner, is_head=False, ordered=self.ordered)
        self.scanner.add_token(list_end)

    def as_html(self, renderer):
        tag = 'ol' if self.ordered else 'ul'
        if self.is_head:
            return renderer.open_tag(tag)
        return renderer.close_tag(tag, breakline=False)


class Paragraph(BlockToken):
    regex = re.compile(
        r'^((?:[^\n]+\n?(?!'
        r'%s|%s|%s|%s|%s|%s|%s|%s|%s'
        r'))+)\n*' % (
            Fence.pattern().replace(r'\1', r'\2'),
            ListBlock.pattern().replace(r'\1', r'\3'),
            Hrule.pattern(),
            Heading.pattern(),
            LHeading.pattern(),
            BlockQuote.pattern(),
            BlockLink.pattern(),
            BlockFootnote.pattern(),
            '<' + _block_tag,
        )
    )

    def setup(self):
        self.is_head = True
        self.content = self.matchs.group(1).rstrip('\n')
        super(Paragraph, self).setup()
        self.scanner.parse(self.content, self.scanner.default_inline_regex)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)

    def as_html(self, renderer):
        if self.is_head:
            return renderer.open_tag('p')
        return renderer.close_tag('p', breakline=True)


class BlockHtml(BlockToken):
    regex = re.compile(
        r'^ *(?:%s|%s|%s) *(?:\n{2,}|\s*$)' % (
            r'<!--[\s\S]*?-->',
            r'<(%s)((?:%s)*?)>([\s\S]*?)<\/\1>' % (_block_tag, _valid_attr),
            r'<%s(?:%s)*?\s*\/?>' % (_block_tag, _valid_attr),
        )
    )
    html_attrs = None
    tag = None

    def setup(self):
        if not self.matchs.group(1):
            self.content = self.matchs.group(0)
            self.open_tag = True
        else:
            self.open_tag = False
            self.tag = self.matchs.group(1)
            self.html_attrs = self.matchs.group(2)
            self.content = self.matchs.group(3)
        super(BlockHtml, self).setup()

    def as_html(self, renderer):
        if self.open_tag:
            attrs = {}
            for s in self.html_attrs.strip().split():
                k, v = s.split('=')
                attrs[k] = v
            html = renderer.block_html(self.tag, self.content, **attrs)
        else:
            html = self.content
        return renderer.escape(html)


class Table(BlockToken):
    regex = re.compile(
        r'^ *\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n*'
    )

    @property
    def header(self):
        return re.split(r' *\| *', re.sub(r'^ *| *\| *$', '', self.matchs.group(1)))

    @property
    def align(self):
        align = re.split(r' *\| *', re.sub(r' *|\| *$', '', self.matchs.group(2)))
        for index, alg in enumerate(align):
            if re.search(r'^ *:-+ *$', alg):
                align[index] = 'left'
            elif re.search(r'^ *:-+: *$', alg):
                align[index] = 'center'
            elif re.search(r'^ *-+: *$', alg):
                align[index] = 'right'
            else:
                align[index] = None
        return align

    @property
    def cells(self):
        cells = re.sub(r'(?: *\| *)?\n$', '', self.matchs.group(3)).split('\n')
        for index, cell in enumerate(cells):
            cell = re.sub(r'^ *\| *| *\| *$', '', cell)
            cells[index] = re.split(r' *\| *', cell)
        return cells

    def as_html(self, renderer):
        cell = header = body = renderer.placeholder
        for index, value in enumerate(self.header):
            align = self.align[index] if index < len(self.align) else None
            cell += self.format_cell(value, header=True, align=align)
        header += self.format_row(cell)

        for index, row in enumerate(self.cells):
            cell = renderer.placeholder
            for row_index, value in enumerate(row):
                align = self.align[row_index] if row_index < len(self.align) else None
                cell += self.format_cell(value, header=True, align=align)
            body += self.format_row(cell)

        return (
            '<table>\n<thead>%s</thead>\n'
            '<tbody>\n%s</tbody>\n</table>\n'
        ) % (header, body)

    def format_row(self, content):
        return '<tr>\n%s</tr>\n' % content

    def format_cell(self, content, **options):
        '''
        return a table cell
        '''
        if options.get('header'):
            tag = 'th'
        else:
            tag = 'td'
        if options.get('align'):
            return '<%s style="text-align:%s">%s</%s>\n' % (tag, options['align'], content, tag)
        return '<%s>%s</%s>\n' % (tag, content, tag)


class NpTable(Table):
    regex = re.compile(
        r'^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n*'
    )

    @property
    def cells(self):
        cells = re.sub(r'\n$', '', self.matchs.group(3)).split('\n')
        for index, cell in enumerate(cells):
            cells[index] = re.split(r' *\| *', cell)
        return cells


class BlockText(BlockToken):
    regex = re.compile(r'^[^\n]+')

    def setup(self):
        self.is_head = True
        self.content = self.matchs.group(0)
        super(BlockText, self).setup()
        self.scanner.parse(self.content, self.scanner.default_inline_regex)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)

    def as_html(self, renderer):
        if self.is_head:
            return renderer.open_tag('p')
        return renderer.close_tag('p', breakline=True)


# ########## InlineTokens ################ #


class Escape(InlineToken):
    regex = re.compile(r'^\\([\\`*{}\[\]()#+\-.!_>~|])')  # \* \+ \! ....

    def as_html(self, renderer):
        return renderer.escape(self.matchs.group(1))


class InlineHtml(InlineToken):
    _tags = [
        'a', 'em', 'strong', 'small', 's', 'cite', 'q', 'dfn', 'abbr', 'data',
        'time', 'code', 'var', 'samp', 'kbd', 'sub', 'sup', 'i', 'b', 'u', 'mark',
        'ruby', 'rt', 'rp', 'bdi', 'bdo', 'span', 'br', 'wbr', 'ins', 'del',
        'img', 'font',
    ]
    regex = re.compile(
        r'^(?:%s|%s|%s)' % (
            r'<!--[\s\S]*?-->',
            r'<(\w+%s)((?:%s)*?)\s*>([\s\S]*?)<\/\1>' % (_valid_end, _valid_attr),
            r'<\w+%s(?:%s)*?\s*\/?>' % (_valid_end, _valid_attr),
        )
    )

    def setup(self):
        self.is_head = True
        self.tag = self.matchs.group(1)
        if self.tag not in self._tags:
            return
        self.extra = self.matchs.group(2) or ''
        self.content = self.matchs.group(3)
        super(InlineHtml, self).setup()
        self.scanner.parse(self.content, self.scanner.inline_htmls)
        tail = self._clone()
        tail.is_head = False
        self.scanner.add_token(tail)

    def as_html(self, renderer):
        if self.is_head:
            return '<{tag}{ext}>'.format(tag=self.tag, ext=self.extra)
        return '</%s>' % self.tag


class InlineAutoLink(InlineToken):
    regex = re.compile(r'^<([^ >]+(@|:)[^ >]+)>')

    def as_html(self, renderer):
        link = renderer.escape(self.matchs.group(1))
        addr = 'mailto:%s' % link if self.matchs.group(2) == '@' else ''
        return renderer.link(addr, link)


class InlineLink(InlineToken):
    regex = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\('
        r'''\s*(<)?([\s\S]*?)(?(2)>)(?:\s+['"]([\s\S]*?)['"])?\s*'''
        r'\)'
    )
    is_head = None

    def setup(self):
        self.line = self.matchs.group(0)
        self.content = self.matchs.group(1)
        self.link = self.matchs.group(3)
        self.title = self.matchs.group(4) or ''
        # if it's not an image link, keep parsing the content
        if self.line[0] != '!':
            self.is_head = True
            self.scanner.add_token(self)
            self.scanner.parse(self.content, self.scanner.default_inline_regex)
            tail = self._clone()
            tail.is_head = False
            self.scanner.add_token(tail)
        else:
            self.scanner.add_token(self)

    def as_html(self, renderer):
        if self.is_head is None:
            if self.title:
                return renderer.img(self.link, self.content, self.title)
            else:
                return renderer.img(self.link, alt=self.content)
        elif self.is_head:
            output = '<a href=%s>' % self.link
        else:
            output = '</a>'
        return output


class InlineRefLink(InlineToken):
    regex = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\s*\[([^^\]]*)\]'
    )

    def setup(self):
        self.ref_key = self._shrink_blank_characters(self.matchs.group(2) or self.matchs.group(1))
        self.title = self.matchs.group(1) or self.matchs.group(2)
        super(InlineRefLink, self).setup()

    def as_html(self, renderer):
        links = filter(lambda x: x.ref_key == self.ref_key, self.scanner.links)
        if not links:
            return ''
        link = links[-1].link
        return renderer.link(link, self.title)


class InlineNolink(InlineToken):
    regex = re.compile(r'^!?\[((?:\[[^\]]*\]|[^\[\]])*)\]')

    def as_html(self, renderer):
        return renderer.link('#', self.matchs.group(0))


class InlineUrl(InlineToken):
    regex = re.compile(r'''^(https?:\/\/[^\s<]+[^<.,:;"')\]\s])''')

    def as_html(self, renderer):
        return renderer.escape(self.matchs.group(1))


class DoubleEmphasis(InlineToken):
    regex = re.compile(
        r'^_{2}([\s\S]+?)_{2}(?!_)'
        r'|'
        r'^\*{2}([\s\S]+?)\*{2}(?!\*)'
    )

    def as_html(self, renderer):
        return renderer.double_emphasis(self.matchs.group(2) or self.matchs.group(1))


class Emphasis(InlineToken):
    regex = re.compile(
        r'^\b_((?:__|[^_])+?)_\b'
        r'|'
        r'^\*((?:\*\*|[^\*])+?)\*(?!\*)'
    )

    def as_html(self, renderer):
        return renderer.emphasis(self.matchs.group(2) or self.matchs.group(1))


class Code(InlineToken):
    regex = re.compile(r'^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)')

    def as_html(self, renderer):
        content = renderer.escape(self.matchs.group(2), smart_amp=False)
        return renderer.code(content)


class LineBreak(InlineToken):
    regex = re.compile(r'^ {2,}\n(?!\s*$)')

    def as_html(self, renderer):
        return renderer.line_break


class StrikeThrough(InlineToken):
    '''
    strikethrough like ~~text~~
    '''
    regex = re.compile(r'^~~(?=\S)([\s\S]*?\S)~~')

    def as_html(self, renderer):
        return renderer.strikethrough(self.matchs.group(1))


class InlineFootnote(InlineToken):
    regex = re.compile(r'^\[\^([^\]]+)\]')

    def setup(self):
        self.ref_key = self._shrink_blank_characters(self.matchs.group(1))
        super(InlineFootnote, self).setup()
        inline_footnotes = filter(
            lambda x: isinstance(x, InlineFootnote), self.scanner.tokens)
        self.index = inline_footnotes.index(self) + 1

    def as_html(self, renderer):
        ref_footnote = filter(
            lambda x: isinstance(x, BlockFootnote) and
            x.key == self.ref_key, self.scanner.footnotes)
        if not ref_footnote:
            return renderer.placeholder
        return renderer.footnote_ref(self.ref_key, self.index)


class InlineText(InlineToken):
    regex = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| {2,}\n|$)')

    def as_html(self, renderer):
        return renderer.escape(self.matchs.group(0))


blocks_default = [
    NewLine, Hrule, BlockCode, Fence, Heading, NpTable, LHeading, BlockQuote, ListBlock,
    BlockHtml, BlockLink, BlockFootnote, Table, Paragraph, BlockText
]


list_items = [
    NewLine, BlockCode, Fence, LHeading, Hrule, BlockQuote, ListBlock, BlockHtml, BlockText
]


block_footnotes = [
    NewLine, BlockCode, Fence, Heading, NpTable, LHeading, Hrule, BlockQuote, ListBlock,
    BlockHtml, Table, Paragraph, BlockText
]


inlines_default = [
    Escape, InlineHtml, InlineAutoLink, InlineUrl, InlineFootnote, InlineLink, InlineRefLink,
    InlineNolink, DoubleEmphasis, Emphasis, Code, LineBreak, StrikeThrough, InlineText
]


inline_htmls = [
    Escape, InlineAutoLink, InlineUrl, InlineLink, InlineRefLink, InlineNolink, DoubleEmphasis,
    Emphasis, Code, LineBreak, StrikeThrough, InlineText
]
