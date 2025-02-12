import scrapy


class CatalogSpider(scrapy.Spider):
    name = "catalog"
    allowed_domains = ["remex.ru"]
    start_urls = ["https://remex.ru"]

    def start_requests(self):
        return super().start_requests()



    def parse(self, response, **kwargs):
        pass
