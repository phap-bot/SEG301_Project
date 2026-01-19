from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key='fc-1e46b8ad34ca4a16aaecc43d58e26613')

# Crawl with scrape options
response = firecrawl.crawl('https://www.lazada.vn/',
    limit=100,
    scrape_options={
        'formats': [
            'markdown',
            { 'type': 'json', 'schema': { 'type': 'object', 'properties': { 'title': { 'type': 'string' } } } }
        ],
        'proxy': 'auto',
        'maxAge': 600000,
        'onlyMainContent': True
    }
)
{
  "success": true,
  "id": "123-456-789",
  "url": "https://api.firecrawl.dev/v2/crawl/123-456-789"
}
status = firecrawl.get_crawl_status("<crawl-id>")
print(status)