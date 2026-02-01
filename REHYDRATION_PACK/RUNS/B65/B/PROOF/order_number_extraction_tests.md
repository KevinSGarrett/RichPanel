## Order number extraction tests (B65/B)

### Added unit cases (expected outcomes)
- `Order # 1180306` -> extract `1180306` (explicit order pattern).
- `#1180306` -> extract `1180306` (hash pattern with 6-10 digits).
- `<a href="#m_12345">Click</a>` -> extract nothing (HTML stripped; anchor noise ignored).
- `Order # 1180306 ref #9999999` -> extract `1180306` (prefer order-word pattern over hash).

### Redacted B64/C sample checks (noise resistance)
Source: `REHYDRATION_PACK/RUNS/B64/C/PROOF/prod_shadow_manual_review.json`
- Excerpt: `order <redacted> a href="<redacted>" target="_blank" ...`  
  Evidence run (synthetic order number inserted; anchor preserved):  
  `order #1180306 <a href="#m_12345" target="_blank">Sent from Yahoo Mail</a>`

Evidence output:
```text
{'name': 'b64c_anchor_noise', 'source': 'B64/C manual review redacted anchor excerpt', 'message': 'order #1180306 <a href="#m_12345" target="_blank">Sent from Yahoo Mail</a>', 'extracted_order_number': '1180306', 'routing_intent': 'unknown_other', 'routing_reason': 'no strong intent keyword detected'}
```
