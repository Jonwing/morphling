# coding: utf-8
import collections
import re
from .utils import (
    _pure_pattern, _keyify, _block_tag, _valid_attr, _block_code_leading_pattern,
    _block_quote_leading_pattern, _valid_end, _inline_tags
)
from .token import blocks_default, list_items, block_footnotes, inlines_default, inline_htmls


class BlockScanner(object):
    '''
    BlockScanner
    '''
    default_regex = blocks_default
    list_regex = list_items
    footnote_regex = block_footnotes

    def __init__(self):
        self.tokens = collections.deque()

    def parse(self, source, regexs=None):
        source = source.rstrip('\n')
        regexs = regexs or self.default_regex

        while source:
            match = None
            for token_class in regexs:
                match = token_class.match(source, scanner=self)
                if match:
                    break
            if match:
                # self.tokens.append(match) Token implements this function
                source = source[match.length:]
            else:
                raise RuntimeError('Not match any token')

        return self.tokens


class Scanner(object):
    '''
    '''
    # default regex: parse default blocks
    default_regex = blocks_default

    # list_regex: parse list items
    list_regex = list_items

    # footnote_regex: parse footnote
    footnote_regex = block_footnotes

    # default_inline_regex: parse default inline objects
    default_inline_regex = inlines_default

    # inline_htmls: parse inline html elements
    inline_htmls = inline_htmls

    def __init__(self):
        self.tokens = collections.deque()

    def parse(self, source, regexs=None):
        source = source.rstrip('\n')
        regexs = regexs or self.default_regex

        while source:
            match = None
            for token_class in regexs:
                match = token_class.match(source, scanner=self)
                if match:
                    break
            if match:
                # self.tokens.append(match) Token implements this function
                source = source[match.length:]
            else:
                raise RuntimeError('Not match any token')

        return self.tokens

    def add_token(self, token):
        self.tokens.append(token)


class InlineScanner(BlockScanner):
    '''
    InlineScanner
    '''
    default_regex = inlines_default
    inline_htmls = inline_htmls

    def parse_to_html(self, source, regexs=None):
        self.tokens.clear()
        self.parse(source, regexs=regexs)
        return ''.join(
            [token.as_html(scanner=InlineScanner()) for token in self.tokens])


class BlockGrammar(object):
    """Grammars for block level tokens."""

    def_links = re.compile(
        r'^ *\[([^^\]]+)\]: *'  # [key]:
        r'<?([^\s>]+)>?'  # <link> or link
        r'(?: +["(]([^\n]+)[")])? *(?:\n+|$)'
    )
    def_footnotes = re.compile(
        r'^\[\^([^\]]+)\]: *('
        r'[^\n]*(?:\n+|$)'  # [^key]:
        r'(?: {1,}[^\n]*(?:\n+|$))*'
        r')'
    )

    newline = re.compile(r'^\n+')
    block_code = re.compile(r'^( {4}[^\n]+\n*)+')
    fences = re.compile(
        r'^ *(`{3,}|~{3,}) *(\S+)? *\n'  # ```lang
        r'([\s\S]+?)\s*'
        r'\1 *(?:\n+|$)'  # ```
    )
    hrule = re.compile(r'^ {0,3}[-*_](?: *[-*_]){2,} *(?:\n+|$)')
    heading = re.compile(r'^ *(#{1,6}) *([^\n]+?) *#* *(?:\n+|$)')
    lheading = re.compile(r'^([^\n]+)\n *(=|-)+ *(?:\n+|$)')
    block_quote = re.compile(r'^( *>[^\n]+(\n[^\n]+)*\n*)+')
    list_block = re.compile(
        r'^( *)([*+-]|\d+\.) [\s\S]+?'
        r'(?:'
        r'\n+(?=\1?(?:[-*_] *){3,}(?:\n+|$))'  # hrule
        r'|\n+(?=%s)'  # def links
        r'|\n+(?=%s)'  # def footnotes
        r'|\n{2,}'
        r'(?! )'
        r'(?!\1(?:[*+-]|\d+\.) )\n*'
        r'|'
        r'\s*$)' % (
            _pure_pattern(def_links),
            _pure_pattern(def_footnotes),
        )
    )
    list_item = re.compile(
        r'^(( *)(?:[*+-]|\d+\.) [^\n]*'
        r'(?:\n(?!\2(?:[*+-]|\d+\.) )[^\n]*)*)',
        flags=re.M
    )
    list_bullet = re.compile(r'^ *(?:[*+-]|\d+\.) +')
    paragraph = re.compile(
        r'^((?:[^\n]+\n?(?!'
        r'%s|%s|%s|%s|%s|%s|%s|%s|%s'
        r'))+)\n*' % (
            _pure_pattern(fences).replace(r'\1', r'\2'),
            _pure_pattern(list_block).replace(r'\1', r'\3'),
            _pure_pattern(hrule),
            _pure_pattern(heading),
            _pure_pattern(lheading),
            _pure_pattern(block_quote),
            _pure_pattern(def_links),
            _pure_pattern(def_footnotes),
            '<' + _block_tag,
        )
    )
    block_html = re.compile(
        r'^ *(?:%s|%s|%s) *(?:\n{2,}|\s*$)' % (
            r'<!--[\s\S]*?-->',
            r'<(%s)((?:%s)*?)>([\s\S]*?)<\/\1>' % (_block_tag, _valid_attr),
            r'<%s(?:%s)*?\s*\/?>' % (_block_tag, _valid_attr),
        )
    )
    table = re.compile(
        r'^ *\|(.+)\n *\|( *[-:]+[-| :]*)\n((?: *\|.*(?:\n|$))*)\n*'
    )
    nptable = re.compile(
        r'^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)\n*'
    )
    text = re.compile(r'^[^\n]+')


class BlockLexer(object):
    """Block level lexer for block grammars."""
    grammar_class = BlockGrammar

    default_rules = [
        'newline', 'hrule', 'block_code', 'fences', 'heading',
        'nptable', 'lheading', 'block_quote',
        'list_block', 'block_html', 'def_links',
        'def_footnotes', 'table', 'paragraph', 'text'
    ]

    list_rules = (
        'newline', 'block_code', 'fences', 'lheading', 'hrule',
        'block_quote', 'list_block', 'block_html', 'text',
    )

    footnote_rules = (
        'newline', 'block_code', 'fences', 'heading',
        'nptable', 'lheading', 'hrule', 'block_quote',
        'list_block', 'block_html', 'table', 'paragraph', 'text'
    )

    def __init__(self, rules=None, **kwargs):
        self.tokens = collections.deque()
        self.def_links = {}
        self.def_footnotes = {}

        if not rules:
            rules = self.grammar_class()

        self.rules = rules

    def __call__(self, text, rules=None):
        # print("parsing text")
        return self.parse(text, rules)

    def parse(self, text, rules=None):
        text = text.rstrip('\n')

        if not rules:
            rules = self.default_rules

        def manipulate(text):
            for key in rules:
                rule = getattr(self.rules, key)
                m = rule.match(text)
                if not m:
                    continue
                getattr(self, 'parse_%s' % key)(m)
                return m
            return False  # pragma: no cover

        while text:
            m = manipulate(text)
            if m is not False:
                text = text[len(m.group(0)):]
                continue
            if text:  # pragma: no cover
                raise RuntimeError('Infinite loop at: %s' % text)
        return self.tokens

    def parse_newline(self, m):
        # print("parsing new line")
        length = len(m.group(0))
        if length > 1:
            self.tokens.append({'type': 'newline'})

    def parse_block_code(self, m):
        # clean leading whitespace
        code = _block_code_leading_pattern.sub('', m.group(0))
        # print "parsing block code:", code
        self.tokens.append({
            'type': 'code',
            'lang': None,
            'text': code,
        })

    def parse_fences(self, m):
        # print "fences: ", m.group(3)
        self.tokens.append({
            'type': 'code',
            'lang': m.group(2),
            'text': m.group(3),
        })

    def parse_heading(self, m):
        # print "heading: ", m.group(2)
        self.tokens.append({
            'type': 'heading',
            'level': len(m.group(1)),
            'text': m.group(2),
        })

    def parse_lheading(self, m):
        """Parse setext heading."""
        # print "setext heading: ", m.group(1)
        self.tokens.append({
            'type': 'heading',
            'level': 1 if m.group(2) == '=' else 2,
            'text': m.group(1),
        })

    def parse_hrule(self, m):
        self.tokens.append({'type': 'hrule'})

    def parse_list_block(self, m):
        bull = m.group(2)
        self.tokens.append({
            'type': 'list_start',
            'ordered': '.' in bull,
        })
        cap = m.group(0)
        self._process_list_item(cap, bull)
        self.tokens.append({'type': 'list_end'})

    def _process_list_item(self, cap, bull):
        cap = self.rules.list_item.findall(cap)

        _next = False
        length = len(cap)

        for i in range(length):
            item = cap[i][0]

            # remove the bullet
            space = len(item)
            item = self.rules.list_bullet.sub('', item)

            # outdent
            if '\n ' in item:
                space = space - len(item)
                pattern = re.compile(r'^ {1,%d}' % space, flags=re.M)
                item = pattern.sub('', item)

            # determine whether item is loose or not
            loose = _next
            if not loose and re.search(r'\n\n(?!\s*$)', item):
                loose = True

            rest = len(item)
            if i != length - 1 and rest:
                _next = item[rest - 1] == '\n'
                if not loose:
                    loose = _next

            if loose:
                t = 'loose_item_start'
            else:
                t = 'list_item_start'

            self.tokens.append({'type': t})
            # recurse
            self.parse(item, self.list_rules)
            self.tokens.append({'type': 'list_item_end'})

    def parse_block_quote(self, m):
        self.tokens.append({'type': 'block_quote_start'})
        # clean leading >
        cap = _block_quote_leading_pattern.sub('', m.group(0))
        self.parse(cap)
        self.tokens.append({'type': 'block_quote_end'})

    def parse_def_links(self, m):
        key = _keyify(m.group(1))
        self.def_links[key] = {
            'link': m.group(2),
            'title': m.group(3),
        }

    def parse_def_footnotes(self, m):
        key = _keyify(m.group(1))
        if key in self.def_footnotes:
            # footnote is already defined
            return

        self.def_footnotes[key] = 0

        self.tokens.append({
            'type': 'footnote_start',
            'key': key,
        })

        text = m.group(2)

        if '\n' in text:
            lines = text.split('\n')
            whitespace = None
            for line in lines[1:]:
                space = len(line) - len(line.lstrip())
                if space and (not whitespace or space < whitespace):
                    whitespace = space
            newlines = [lines[0]]
            for line in lines[1:]:
                newlines.append(line[whitespace:])
            text = '\n'.join(newlines)

        self.parse(text, self.footnote_rules)

        self.tokens.append({
            'type': 'footnote_end',
            'key': key,
        })

    def parse_table(self, m):
        item = self._process_table(m)

        cells = re.sub(r'(?: *\| *)?\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            v = re.sub(r'^ *\| *| *\| *$', '', v)
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.tokens.append(item)

    def parse_nptable(self, m):
        item = self._process_table(m)

        cells = re.sub(r'\n$', '', m.group(3))
        cells = cells.split('\n')
        for i, v in enumerate(cells):
            cells[i] = re.split(r' *\| *', v)

        item['cells'] = cells
        self.tokens.append(item)

    def _process_table(self, m):
        header = re.sub(r'^ *| *\| *$', '', m.group(1))
        header = re.split(r' *\| *', header)
        align = re.sub(r' *|\| *$', '', m.group(2))
        align = re.split(r' *\| *', align)

        for i, v in enumerate(align):
            if re.search(r'^ *-+: *$', v):
                align[i] = 'right'
            elif re.search(r'^ *:-+: *$', v):
                align[i] = 'center'
            elif re.search(r'^ *:-+ *$', v):
                align[i] = 'left'
            else:
                align[i] = None

        item = {
            'type': 'table',
            'header': header,
            'align': align,
        }
        return item

    def parse_block_html(self, m):
        tag = m.group(1)
        if not tag:
            text = m.group(0)
            self.tokens.append({
                'type': 'close_html',
                'text': text
            })
        else:
            attr = m.group(2)
            text = m.group(3)
            self.tokens.append({
                'type': 'open_html',
                'tag': tag,
                'extra': attr,
                'text': text
            })
        # print "parsing block html,: ", text

    def parse_paragraph(self, m):
        text = m.group(1).rstrip('\n')
        self.tokens.append({'type': 'paragraph', 'text': text})

    def parse_text(self, m):
        text = m.group(0)
        # print "text: ", text
        self.tokens.append({'type': 'text', 'text': text})


class InlineGrammar(object):
    """Grammars for inline level tokens."""

    escape = re.compile(r'^\\([\\`*{}\[\]()#+\-.!_>~|])')  # \* \+ \! ....
    inline_html = re.compile(
        r'^(?:%s|%s|%s)' % (
            r'<!--[\s\S]*?-->',
            r'<(\w+%s)((?:%s)*?)\s*>([\s\S]*?)<\/\1>' % (_valid_end, _valid_attr),
            r'<\w+%s(?:%s)*?\s*\/?>' % (_valid_end, _valid_attr),
        )
    )
    autolink = re.compile(r'^<([^ >]+(@|:)[^ >]+)>')
    link = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\('
        r'''\s*(<)?([\s\S]*?)(?(2)>)(?:\s+['"]([\s\S]*?)['"])?\s*'''
        r'\)'
    )
    reflink = re.compile(
        r'^!?\[('
        r'(?:\[[^^\]]*\]|[^\[\]]|\](?=[^\[]*\]))*'
        r')\]\s*\[([^^\]]*)\]'
    )
    nolink = re.compile(r'^!?\[((?:\[[^\]]*\]|[^\[\]])*)\]')
    url = re.compile(r'''^(https?:\/\/[^\s<]+[^<.,:;"')\]\s])''')
    double_emphasis = re.compile(
        r'^_{2}([\s\S]+?)_{2}(?!_)'  # __word__
        r'|'
        r'^\*{2}([\s\S]+?)\*{2}(?!\*)'  # **word**
    )
    emphasis = re.compile(
        r'^\b_((?:__|[^_])+?)_\b'  # _word_
        r'|'
        r'^\*((?:\*\*|[^\*])+?)\*(?!\*)'  # *word*
    )
    code = re.compile(r'^(`+)\s*([\s\S]*?[^`])\s*\1(?!`)')  # `code`
    linebreak = re.compile(r'^ {2,}\n(?!\s*$)')
    strikethrough = re.compile(r'^~~(?=\S)([\s\S]*?\S)~~')  # ~~word~~
    footnote = re.compile(r'^\[\^([^\]]+)\]')
    text = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| {2,}\n|$)')

    def hard_wrap(self):
        """Grammar for hard wrap linebreak. You don't need to add two
        spaces at the end of a line.
        """
        self.linebreak = re.compile(r'^ *\n(?!\s*$)')
        self.text = re.compile(
            r'^[\s\S]+?(?=[\\<!\[_*`~]|https?://| *\n|$)'
        )


class InlineLexer(object):
    """Inline level lexer for inline grammars."""
    grammar_class = InlineGrammar

    default_rules = [
        'escape', 'inline_html', 'autolink', 'url',
        'footnote', 'link', 'reflink', 'nolink',
        'double_emphasis', 'emphasis', 'code',
        'linebreak', 'strikethrough', 'text',
    ]
    inline_html_rules = [
        'escape', 'autolink', 'url', 'link', 'reflink',
        'nolink', 'double_emphasis', 'emphasis', 'code',
        'linebreak', 'strikethrough', 'text',
    ]

    def __init__(self, renderer, rules=None, **kwargs):
        self.renderer = renderer
        self.links = {}
        self.footnotes = {}
        self.footnote_index = 0

        if not rules:
            rules = self.grammar_class()

        kwargs.update(self.renderer.options)
        if kwargs.get('hard_wrap'):
            rules.hard_wrap()

        self.rules = rules

        self._in_link = False
        self._in_footnote = False
        self._parse_inline_html = kwargs.get('parse_inline_html')

    def __call__(self, text, rules=None):
        return self.output(text, rules)

    def setup(self, links, footnotes):
        self.footnote_index = 0
        self.links = links or {}
        self.footnotes = footnotes or {}

    def output(self, text, rules=None):
        text = text.rstrip('\n')
        if not rules:
            rules = list(self.default_rules)

        if self._in_footnote and 'footnote' in rules:
            rules.remove('footnote')

        output = self.renderer.placeholder()

        def manipulate(text):
            for key in rules:
                pattern = getattr(self.rules, key)
                m = pattern.match(text)
                if not m:
                    continue
                self.line_match = m
                out = getattr(self, 'output_%s' % key)(m)
                if out is not None:
                    return m, out
            return False  # pragma: no cover

        self.line_started = False
        while text:
            ret = manipulate(text)
            self.line_started = True
            if ret is not False:
                m, out = ret
                output += out
                text = text[len(m.group(0)):]
                continue
            if text:  # pragma: no cover
                raise RuntimeError('Infinite loop at: %s' % text)

        return output

    def output_escape(self, m):
        text = m.group(1)
        return self.renderer.escape(text)

    def output_autolink(self, m):
        link = m.group(1)
        if m.group(2) == '@':
            is_email = True
        else:
            is_email = False
        return self.renderer.autolink(link, is_email)

    def output_url(self, m):
        link = m.group(1)
        if self._in_link:
            return self.renderer.text(link)
        return self.renderer.autolink(link, False)

    def output_inline_html(self, m):
        tag = m.group(1)
        if self._parse_inline_html and tag in _inline_tags:
            text = m.group(3)
            if tag == 'a':
                self._in_link = True
                text = self.output(text, rules=self.inline_html_rules)
                self._in_link = False
            else:
                text = self.output(text, rules=self.inline_html_rules)
            extra = m.group(2) or ''
            html = '<%s%s>%s</%s>' % (tag, extra, text, tag)
        else:
            html = m.group(0)
        return self.renderer.inline_html(html)

    def output_footnote(self, m):
        key = _keyify(m.group(1))
        if key not in self.footnotes:
            return None
        if self.footnotes[key]:
            return None
        self.footnote_index += 1
        self.footnotes[key] = self.footnote_index
        return self.renderer.footnote_ref(key, self.footnote_index)

    def output_link(self, m):
        return self._process_link(m, m.group(3), m.group(4))

    def output_reflink(self, m):
        key = _keyify(m.group(2) or m.group(1))
        if key not in self.links:
            return None
        ret = self.links[key]
        return self._process_link(m, ret['link'], ret['title'])

    def output_nolink(self, m):
        key = _keyify(m.group(1))
        if key not in self.links:
            return None
        ret = self.links[key]
        return self._process_link(m, ret['link'], ret['title'])

    def _process_link(self, m, link, title=None):
        line = m.group(0)
        text = m.group(1)
        if line[0] == '!':
            return self.renderer.image(link, title, text)

        self._in_link = True
        text = self.output(text)
        self._in_link = False
        return self.renderer.link(link, title, text)

    def output_double_emphasis(self, m):
        text = m.group(2) or m.group(1)
        text = self.output(text)
        return self.renderer.double_emphasis(text)

    def output_emphasis(self, m):
        text = m.group(2) or m.group(1)
        text = self.output(text)
        return self.renderer.emphasis(text)

    def output_code(self, m):
        text = m.group(2)
        return self.renderer.codespan(text)

    def output_linebreak(self, m):
        return self.renderer.linebreak()

    def output_strikethrough(self, m):
        text = self.output(m.group(1))
        return self.renderer.strikethrough(text)

    def output_text(self, m):
        text = m.group(0)
        return self.renderer.text(text)
