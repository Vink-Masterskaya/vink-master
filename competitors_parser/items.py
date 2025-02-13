import scrapy


class CompetitorsParserItem(scrapy.Item):
    category = scrapy.Field()
    name = scrapy.Field()
    unit = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    url = scrapy.Field()
