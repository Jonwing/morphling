# -*- coding: utf-8 -*-

from morphling.renderer import Renderer
from morphling.scanner import Scanner


class MarkdownParser(object):
    '''
    The default markdown parser that combines the default scanner and the default renderer.
    There is an instance "morphling.mdp" that just simply initialized this class without params.
        :params scanner: an instance of morphling.scanner.Scanner
        :params renderer: an instance of morphling.renderer.Renderer
        :params source_path(string): set if you want to parse from a markdown file
        :params output_path(string): set if you need to output the parsed content as a file
    '''
    scanner_class = Scanner
    renderer_class = Renderer

    def __init__(self, scanner=None, renderer=None, **kwargs):
        self.source_path = kwargs.pop('source_path', None)
        self.output_path = kwargs.pop('output_path', None)
        self._scanner = scanner or self.scanner_class()
        self._renderer = renderer or self.renderer_class(**kwargs)

    def _parse(self, content):
        self._scanner.clear()
        self._scanner.parse(content)

    def parse_file(self, path=None):
        '''
        parse markdown file
        params:
            :path:  location of markdown file
        '''
        if path is None and self.source_path is None:
            raise ValueError("invalid path")
        path = path or self.source_path
        with open(path, 'r') as source:
            content = source.read()
        return self.parse(content)

    def parse(self, content):
        '''
        parse markdown content
        params:
            :content: text content in markdown language
        '''
        self._parse(content)
        self.output = ''.join(
            map(lambda t: t.as_html(self._renderer), self._scanner.all_tokens))
        if self.output_path:
            with open(self.output_path, 'w') as f:
                f.write(self.output)


mdp = MarkdownParser()
