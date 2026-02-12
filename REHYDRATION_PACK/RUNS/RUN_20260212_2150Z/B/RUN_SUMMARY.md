# RUN_SUMMARY

- Goal: add Shopify order tags to order summary (extraction only).
- Scope: backend order lookup and fixtures/tests.
- Added `order_tags_raw` and `order_tags` extraction.
- Tags parsed with trim + stable dedupe.
- Shopify order field list now requests tags.
- Tests updated for tag extraction.
- No ETA logic changes.
- No routing or messaging changes.
- No outbound writes.
- Ready for follow-up ETA logic PR.
