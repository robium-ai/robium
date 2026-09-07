# Choosing Foxglove or Lichtblick

Both clients support the common local workflow: connect to a Foxglove
WebSocket, inspect live ROS 2 data, open recordings, arrange panels, and use
extensions. Choose from the ownership model and services you need.

- **Choose Lichtblick** when the viewer must be inspectable, run locally or
  offline, be hosted as part of the application, or ship a custom panel without
  depending on a managed vendor service. It publishes desktop and browser
  clients and packages TypeScript extensions as `.foxe` files.
- **Choose Foxglove** when managed recordings, search, fleet access,
  organization layouts, or vendor support are material requirements.
- **Check the current contract** before promising a self-hosted Foxglove viewer.
  On 2026-08-27 the current embedded/self-hosted path required a custom
  Enterprise agreement; this is volatile commercial information, not a
  permanent product property.
- A launcher deep link can preselect a data source, but an organization layout
  identifier must already exist in that organization. It is not a way to embed
  arbitrary layout JSON in a URL.

Robium's Robot Navigation application validated a pinned Lichtblick web build,
a bundled `.foxe` dashboard extension, committed mapping/navigation layouts,
and a bridge at `ws://localhost:8765`. That is evidence for the tested app, not
a requirement to use the same port, build, or layout elsewhere.

Start from the current upstream sources:

- [Lichtblick repository](https://github.com/Lichtblick-Suite/lichtblick)
- [Lichtblick live-data documentation](https://lichtblick-suite.github.io/docs/docs/connecting-to-data/live-data/)
- [Lichtblick extensions](https://lichtblick-suite.github.io/docs/docs/extensions/introduction/)
- [Foxglove documentation](https://docs.foxglove.dev/docs)
- [Foxglove self-hosted viewer documentation](https://docs.foxglove.dev/docs/embed/self-hosted)
- [Robot Navigation](https://github.com/robium-ai/robium-apps/tree/main/robot-navigation)
