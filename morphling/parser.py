# -*- coding: utf-8 -*-


class MarkdownParser(object):
    renderer_class = None
    block_scanner_class = None
    inline_scanner_class = None

    def _parse(self, content):
        pass

    def parse_file(self, path, *kwargs):
        '''
        parse markdown file
        params:
            :path:  location of markdown file
        '''
        pass

    def parse(self, content, *kwargs):
        '''
        parse markdown content
        params:
            :content: text content in markdown language
        '''
        pass
