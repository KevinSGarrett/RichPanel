## B74 A — Changes

- Added Secrets Manager bot agent id resolution with env override and hard block if missing.
- Added stable channel detection metadata and read-only guard reporting.
- Updated outbound decision logic to enforce email-only send-message and missing bot id routing.
- Extended dev proof runner fields and unit tests for send-message decision paths.
- Updated `docs/08_Engineering/Richpanel_Reply_Paths.md` to reflect bot id + send-message requirements.
