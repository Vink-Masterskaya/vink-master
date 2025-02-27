import scrapy


class CompetitorsParserItem(scrapy.Item):
    id = scrapy.Field()
    category = scrapy.Field()
    product_id= scrapy.Field()
    name = scrapy.Field()
    unit = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    url = scrapy.Field()
    char = scrapy.Field()
    stocks = scrapy.Field()
