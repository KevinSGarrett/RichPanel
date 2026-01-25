# Changes — B58/A

- `backend/src/richpanel_middleware/automation/pipeline.py`
  - Added email-channel `/send-message` reply path with author resolution.
  - Routed failures to support with explicit reason tags; added loop-prevention tags for close failures after send-message.
  - Added deterministic outbound path tags for send-message vs comment paths.
- `backend/src/richpanel_middleware/automation/llm_routing.py`
  - Removed force-primary confidence threshold bypass.
- `scripts/test_pipeline_handlers.py`
  - Added email send-message, author resolution, close-failure routing, and missing-author tests.
  - Updated comment-path tags and expanded fake executor support.
- `scripts/test_llm_routing.py`
  - Added force-primary threshold coverage tests.
- `docs/03_Richpanel_Integration/Outbound_Reply_Paths.md`
  - Documented outbound reply paths and email-specific requirements.
