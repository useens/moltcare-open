---
name: web-intelligence
description: Extract and analyze web data from multiple sources using unified scraping patterns. Supports structured extraction, content analysis, and data enrichment.
type: data
created: 2026-03-01
author: OpenClaw
---

# Web Intelligence

Unified web data extraction and analysis. Extract structured data from any website, analyze content patterns, and enrich datasets with additional context.

# Prerequisites

- [ ] `.env` file with required API tokens
- [ ] Python >=3.10 with `requests` and `beautifulsoup4`
- [ ] Node.js >=18 with `playwright` (for dynamic sites)
- [ ] Internet connection for external sources

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Define extraction goal and target
- [ ] Step 2: Select extraction method (static/dynamic/API)
- [ ] Step 3: Ask user preferences (format, scope, filters)
- [ ] Step 4: Execute extraction pipeline
- [ ] Step 5: Validate and summarize results
```

### Step 1: Define Extraction Goal

Understand what data the user needs:
- **Content extraction**: Articles, products, reviews
- **Structured data**: Tables, lists, metadata
- **Enrichment**: Add context to existing data

### Step 2: Select Extraction Method

Choose the right approach based on target:

| Target Type | Method | Best For |
|-------------|--------|----------|
| Static HTML | `requests` + `BeautifulSoup` | Simple, fast extraction |
| JavaScript-rendered | `playwright` | Dynamic content, SPAs |
| API endpoint | Direct HTTP | Structured JSON data |
| Rate-limited sites | `scrapy` with delays | Large-scale scraping |
| Anti-bot protected | `playwright` with stealth | Protected sites |

### Step 3: Ask User Preferences

Before executing:

1. **Output format**:
   - **Quick** - Display top 10 results in chat
   - **Markdown** - Structured report with analysis
   - **JSON** - Machine-readable export
   - **CSV** - Tabular data for spreadsheets

2. **Scope limits**:
   - Number of pages/items
   - Time range (if applicable)
   - Depth of following links

3. **Data filters**:
   - Include/exclude patterns
   - Required fields
   - Language/region constraints

### Step 4: Execute Extraction

**Quick extraction (static HTML):**
```python
from core.web_extractor import extract_static

results = extract_static(
    url="https://example.com",
    selectors={
        "title": "h1",
        "content": "article p",
        "date": "time[datetime]"
    }
)
```

**Dynamic content (JavaScript-rendered):**
```python
from core.web_extractor import extract_dynamic

results = extract_dynamic(
    url="https://spa-app.com",
    wait_for=".content-loaded",
    extract={"items": ".product-item"}
)
```

**Batch extraction (multiple URLs):**
```bash
python3 scripts/web-intelligence.py batch \
  --urls urls.txt \
  --config extraction.json \
  --output results.csv
```

### Step 5: Validate and Summarize

After extraction, report:
- Number of items successfully extracted
- Success/failure rate
- File location (if saved)
- Key findings and patterns
- Suggested follow-up analysis

## Output Formats

| Format | Extension | Use Case | Command |
|--------|-----------|----------|---------|
| **Quick** | - | Preview in chat | (no output flag) |
| **JSON** | `.json` | API integration, processing | `--format json` |
| **CSV** | `.csv` | Spreadsheet analysis | `--format csv` |
| **Markdown** | `.md` | Human-readable report | `--format md` |

## Use Case Mapping

| Use Case | Primary Method | Secondary | Chain |
|----------|---------------|-----------|-------|
| **News monitoring** | RSS/API | Static scrape | 1-step |
| **Price tracking** | Static scrape | API fallback | 1-step |
| **Review analysis** | Static scrape | Sentiment analysis | 2-step |
| **Lead enrichment** | Initial scrape | Contact finder | 2-step |
| **Competitor monitoring** | Multi-site scrape | Comparison report | 3-step |

## Multi-Step Workflows

### Workflow: Lead Enrichment

```
Step 1: Extract business listings
        ↓
Step 2: Find contact information
        ↓
Step 3: Validate and format
```

**Command:**
```bash
python3 scripts/web-intelligence.py workflow \
  --name lead-enrichment \
  --input companies.csv \
  --output enriched.csv
```

### Workflow: Content Analysis

```
Step 1: Extract articles/posts
        ↓
Step 2: Analyze sentiment/topics
        ↓
Step 3: Generate summary report
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `TIMEOUT` | Page load too slow | Increase timeout, check connectivity |
| `404_NOT_FOUND` | Page doesn't exist | Verify URL, check for redirects |
| `RATE_LIMITED` | Too many requests | Add delays, use proxy rotation |
| `SELECTOR_NOT_FOUND` | Element not present | Update selectors, check page structure |
| `SSL_ERROR` | Certificate issue | Use `verify=False` (caution) |
| `BLOCKED` | Anti-bot protection | Use `playwright` with stealth mode |
| `PARSING_ERROR` | Invalid HTML/JSON | Add error handling, use fallback |

## Examples

### Example 1: Extract Product Data

```python
from core.web_extractor import extract_static

products = extract_static(
    url="https://store.com/products",
    selectors={
        "name": ".product-title",
        "price": ".product-price",
        "image": ".product-image img[src]"
    },
    output="products.json"
)
```

### Example 2: Monitor Price Changes

```bash
# Save current prices
python3 scripts/web-intelligence.py extract \
  --url "https://store.com/product/123" \
  --selectors '{"price": ".price"}' \
  --output prices/$(date +%Y%m%d).json

# Compare with previous
python3 scripts/web-intelligence.py compare \
  --baseline prices/20260301.json \
  --current prices/20260302.json
```

### Example 3: Batch Article Extraction

```bash
# Create URL list
cat > articles.txt <<EOF
https://blog.com/post-1
https://blog.com/post-2
https://blog.com/post-3
EOF

# Extract all
python3 scripts/web-intelligence.py batch \
  --urls articles.txt \
  --template article_template.json \
  --output articles.csv
```

## Configuration Templates

### article_template.json

```json
{
  "selectors": {
    "title": "h1.article-title",
    "author": ".author-name",
    "date": "time[datetime]",
    "content": ".article-body p",
    "tags": ".tag-list a"
  },
  "transforms": {
    "date": "parse_iso_date",
    "content": "join_paragraphs"
  }
}
```

## Performance Tips

- Use **static extraction** when possible (10x faster)
- Set **appropriate timeouts** based on site speed
- Use **connection pooling** for batch operations
- Implement **caching** to avoid re-fetching
- Add **progress indicators** for long operations
