# coding: utf-8

import re
from itertools import chain
from .token import blocks_default, list_items, block_footnotes, inlines_default, inline_htmls


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
        self._tokens = []
        self._footnotes = []
        self._links = []

    def parse(self, source, regexs=None):
        '''
        to parse(match) the source using the given regexs.
            :params source: the source text
            :params regexs: regex used to match the source
        it iterates the regexs and calls the token's `match` method to
        try to match the source. Once matched, the token will create a
        new instance of itself and add it to the token collection of the
        scanner.
        '''
        source = self.prepare(source.rstrip('\n'))
        regexs = regexs or self.default_regex

        while source:
            match = None
            for token_class in regexs:
                match = token_class.match(source, scanner=self)
                if match:
                    break
            if match:
                # self._tokens.append(match) Token implements this function
                source = source[match.length:]
            else:
                raise RuntimeError('Not match any token')

        return self._tokens

    @property
    def links(self):
        return self._links

    @property
    def footnotes(self):
        return self._footnotes

    @property
    def tokens(self):
        return self._tokens

    def add_token(self, token):
        self._tokens.append(token)

    def add_footnote(self, footnote):
        self._footnotes.append(footnote)

    def add_link(self, link):
        self._links.append(link)

    @property
    def all_tokens(self):
        # no need to include link definitions
        return chain(self._tokens, self.footnotes)

    def move_block_to_footnotes(self, token_class):
        '''
        move the last block to footnote
        '''
        index = -1
        try:
            while not (
                    isinstance(self._tokens[index], token_class) and
                    self._tokens[index].is_head):
                index -= 1
        except IndexError:
            return None
        self._footnotes.extend(self._tokens[index:])
        self._tokens[index:] = []

    def prepare(self, source):
        '''
        do some preparation before parsing
        '''
        newline = re.compile(r'\r\n|\r')
        spaces = re.compile(r'^ +$', re.M)
        procceed = newline.sub('\n', source).expandtabs(4).replace(
            '\u00a0', ' ').replace('\u2424', '\n')
        return spaces.sub('', procceed)

    def clear(self):
        self._tokens = []
        self._links = []
        self._footnotes = []
