const configSchema = {
  type: "object",
  additionalProperties: false,
};

export default {
  id: "holo-rss-reader",
  name: "holo RSS Reader",
  description:
    "RSS/Atom feed reader and daily digest skill with Gist OPML import, full-article caching, and WeChat Official Accounts bridging.",
  configSchema,
  register() {
    // Skill-only plugin wrapper. OpenClaw discovers the actual capabilities from openclaw.plugin.json.
  },
};
