# -*- coding: utf-8 -*-
import os
import os.path
import re
from urllib.parse import unquote
import scrapy


class SiteSpider(scrapy.Spider):
    name = "site"

    # allowed_domains = [TARGET_DOMAIN]
    # start_urls = (
    #     'http://%s/' % TARGET_DOMAIN,
    #     # 'http://%s/about' % TARGET_DOMAIN,
    #     # 'http://%s/wp-content/themes/whale/font-awesome-4.2.0/css/font-awesome.min.css' % TARGET_DOMAIN,
    #     'http://%s/robots.txt' % TARGET_DOMAIN,
    #     'http://%s/sitemap.xml' % TARGET_DOMAIN,
    # )

    custom_settings = dict(
        # DOMAIN='example.com',
        USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36',
        DIR_ROOT='export',
        # USER_AGENT='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36',
    )

    def start_requests(self):
        """
        http://doc.scrapy.org/en/latest/topics/spiders.html#scrapy.spiders.Spider.start_requests
        :return:
        """

        scheme = 'https://' if self.settings.get('HTTPS') else 'http://'
        domain = self.settings.get('DOMAIN')

        # 必须
        assert domain, """
            You must specify the base domain of the site to crawl, by setting
            the DOMAIN setting.
            For example:\n' \
            $ scrapy crawl -s DOMAIN=www.example.com'
            """

        urls = []

        if self.settings.get('START_URLS'):
            urls += self.settings['START_URLS'].split(',')
        else:
            urls.append(scheme + domain)

        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def check_url(self, url):
        """
        判断 url 是否合法，过滤掉特殊的协议 url
        :param url:
        :return:
        """
        # 有冒号的情况下，只有 https:// 和 http:// 是合法的
        if re.match(r'^https?://[^:]+$', url):
            from urllib.parse import urlparse
            url_info = urlparse(url)
            # 只允许爬取本站的链接
            return url_info.netloc == self.settings.get('DOMAIN')
        # 否则带冒号的全部都不是合法的
        if url.find(':') > -1:
            return False
        return True

    def get_request(self, response, url):
        """
        获取应该 yield 的 Request 对象，但是事先做逻辑校验，如果校验失败，
        则返回 None
        :param response:
        :param url:
        :return:
        """
        if self.check_url(url):
            url = response.urljoin(url)
            return scrapy.Request(url, callback=self.parse)

    def get_storage_path(self, response):
        """
        根据文件类型生成存储路径
        :param response:
        :return:
        """

        from urllib.parse import urlparse
        url_info = urlparse(response.url)
        domain = url_info.netloc
        path = url_info.path

        dir_root = self.settings.get('DIR_ROOT')  # + '/' + domain

        # 除了各种认可的静态类型外，其余均作为目录名内嵌 index.html 处理
        if re.search(r'\.(?:js|css|png|jpg|gif|ico|bmp'
                     r'|pdf|docx?|xlsx?|pptx?'
                     r'|zip|txt|svg|eot|woff|ttf|otf|xml|xsl|html?)(?:\?|$)', path):
            full_path = dir_root + path
        else:
            full_path = dir_root + re.sub(r'/$', '', path) + '/index.html'

        # url 转义还原
        full_path = unquote(full_path)

        return full_path

    def parse(self, response):

        print('>>>>>>>> ' + unquote(response.url))

        # ==== 1. 存储文件内容 ====

        # 获取静态化文件存储目录
        full_path = self.get_storage_path(response)
        print('SAVE TO: %s' % os.path.abspath(full_path))

        try:
            # 创建对应的文件夹路径
            os.makedirs(os.path.dirname(full_path), 0o777, True)
            # 写入文件
            with open(full_path, 'wb') as f:
                f.write(response.body)
        except NotADirectoryError:
            import sys
            sys.stderr.write('File write fail: ' + full_path)

        # ==== 2. 解析下一步的动作 ====

        if re.search(r'\.(?:png|jpg|gif|tiff|ico|bmp'
                     r'|pdf|docx?|xlsx?|pptx?'
                     r'|zip|txt|svg|eot|woff|ttf|otf)', full_path):
            return self.parse_binary(response)

        body = response.body.decode('utf8', 'ignore')

        if re.search(r'\.js$', full_path):
            return self.parse_script(response)

        if re.search(r'\.css$', full_path):
            return self.parse_css(response)

        if re.search(r'\.xml$', full_path):
            return self.parse_xml(response)

        if re.search(r'<body', body):
            return self.parse_html(response)

    def parse_html(self, response):

        body = response.body.decode('utf8', 'ignore')

        # 抓取样式里面的 url
        for href in re.findall(r'url\([\'"]?([^)\'"]+)[\'"]?\)', body):
            yield self.get_request(response, href)

        for href in re.findall(r'(?:href|src)="([^"]+)"', body):
            yield self.get_request(response, href)

        for href in re.findall(r'(?:href|src)=\'([^\']+)"', body):
            yield self.get_request(response, href)

        # for href in response.xpath('//@src').extract():
        #     yield self.get_request(response, href)
        #
        # for href in response.xpath('//@href').extract():
        #     yield self.get_request(response, href)

    def parse_xml(self, response):

        body = response.body.decode('utf8', 'ignore')

        for href in re.findall(r'<loc>(.+)</loc>', body):
            yield self.get_request(response, href)

        for href in re.findall(r'href="([^"]+)"', body):
            yield self.get_request(response, href)

    def parse_binary(self, response):
        return

    def parse_css(self, response):

        body = response.body.decode('utf8', 'ignore')

        for href in re.findall(r'url\([\'"]?([^)\'"]+)[\'"]?\)', body):
            yield self.get_request(response, href)

    def parse_script(self, response):
        return
