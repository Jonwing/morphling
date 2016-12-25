# coding: utf-8

from itertools import chain
from .token import blocks_default, list_items, block_footnotes, inlines_default, inline_htmls


class BlockScanner(object):
    '''
    BlockScanner
    deprecated, use Scanner instead.
    '''
    default_regex = blocks_default
    list_regex = list_items
    footnote_regex = block_footnotes

    def __init__(self):
        self.tokens = []

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
    scanner to do the actual parsing job
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
        self.tokens = []
        self._footnotes = []
        self._links = []

    def parse(self, source, regexs=None):
        '''
        to parse(match) the source using the given regexs.
            :params source: the source text
            :params regexs: regex used to try to match the source
        it iterates the regexs and calls the token's `match` method to
        try to match the source. Once matched, the token will create a
        new instance of itself and add it to the token collection of the
        scanner.
        '''
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

    @property
    def links(self):
        return self._links

    @property
    def footnotes(self):
        return self._footnotes

    def add_token(self, token):
        self.tokens.append(token)

    def add_footnote(self, footnote):
        self._footnotes.append(footnote)

    def add_link(self, link):
        self._links.append(link)

    @property
    def all_tokens(self):
        # no need to include link definitions
        return chain(self.tokens, self.footnotes)

    def move_block_to_footnotes(self, token_class):
        '''
        move the last block to footnote
        '''
        index = -1
        try:
            while not (isinstance(self.tokens[index], token_class) and self.tokens[index].is_head):
                index -= 1
        except IndexError:
            return None
        print self.tokens[index:]
        self._footnotes.extend(self.tokens[index:])
        self.tokens[index:] = []

    def prepare(self):
        '''
        do some preparation before parsing
        '''
        pass


class InlineScanner(BlockScanner):
    '''
    InlineScanner
    deprecated, used Scanner instead
    '''
    default_regex = inlines_default
    inline_htmls = inline_htmls

    def parse_to_html(self, source, regexs=None):
        self.tokens.clear()
        self.parse(source, regexs=regexs)
        return ''.join(
            [token.as_html(scanner=InlineScanner()) for token in self.tokens])
