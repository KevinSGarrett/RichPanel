# Tracking Link Generation

## Overview
When order status automation has a carrier + tracking number but no tracking URL,
the system generates a deterministic fallback tracking link for known carriers.
Unknown carriers continue to display `(not available)`.

## Supported carriers and templates
- FedEx: `https://www.fedex.com/fedextrack/?trknbr={tracking_number}`
- UPS: `https://www.ups.com/track?loc=en_US&tracknum={tracking_number}`
- USPS: `https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}`
- DHL: `https://www.dhl.com/global-en/home/tracking/tracking-express.html?submit=1&tracking-id={tracking_number}`

Carrier matching is case-insensitive and uses substring checks (e.g., `"fedex"` in
the carrier string). Tracking numbers are URL-encoded before insertion.

## Fallback behavior
- If `tracking_url` exists, use it unchanged.
- If `tracking_url` is missing but carrier + tracking number exist, generate a
  URL for supported carriers.
- If the carrier is unknown or tracking data is missing, the reply shows
  `Tracking link: (not available)`.

## PII safety
Never log or persist full tracking or order numbers in diagnostics or docs.
Use redacted placeholders in any examples (e.g., `{redacted}`).