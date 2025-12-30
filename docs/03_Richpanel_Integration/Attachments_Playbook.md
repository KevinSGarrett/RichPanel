# Attachments Playbook

Last updated: 2025-12-21

This document will define:
- How we detect attachments and non-text payloads
- How we fetch attachment content safely (size limits, retries)
- How we summarize attachments for LLM (or skip)
- How to avoid payload-too-large failures

Reference: `CommonIssues.zip` attachment-related issues.
