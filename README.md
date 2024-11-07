# LLM Scraper 🕺

A dynamic web-scraper that uses LLMs to extract and analyze web contents.

## How does it work?

We use Beautiful Soup to parse HTML content and send each unique element to an LLM for content analysis. In the final step, we use the results from the LLM to generate triplets, which are then input into a knowledge graph.

| Feature                                                                                                                                                     | Model            |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| WebDriver                                                                                                                                                   | Selenium ✅       |
| HTML Parser                                                                                                                                                 | Beautiful Soup ✅ |
| Knowledge Graph                                                                                                                                             | OpenAI ✅ |
| Analyze Text                                                                                                                                                | OpenAI ✅         |
| Analyze Images                                                                                                                                              | BLIP ✅           |
| Analyze Videos                                                                                                                                              | OpenAI ✅         |
| Analyze Audio Recordings                                                                                                                                    | OpenAI ✅         |
| Analyze Code Snippets                                                                                                                                       | OpenAI ✅         |

