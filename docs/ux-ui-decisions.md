# UX and UI decisions

HoopMetrics treats Fabric App as an interactive product, rather than a set of
report pages. A top-level league view provides context before users drill into
games, teams and players; contextual links and back navigation connect those
views without a persistent sidebar. The latest season and a phase selection
set the context for comparisons.

- **Explore progressively:** standings and leaders lead to team, game and
  player detail; list and calendar modes support different browsing habits.
- **Preserve context:** team pages combine results, statistics and players;
  game pages compare the two sides and expose the underlying box score.
- **Show meaning, not just decoration:** winners and larger comparison values
  receive stronger visual emphasis, while missing values use an explicit dash.
  Comparison direction alone should not be interpreted as a universally
  positive outcome for every statistic.
- **Make controls legible:** shared tabs and segmented controls use a blue
  accent and animated selection, with keyboard focus styling and a reduced
  motion rule. Responsive breakpoints rearrange the layout on smaller screens;
  no claim of formal accessibility certification is made.
- **Expose uncertainty:** the snapshot timestamp, non-official standings,
  derived roster, ESPN-dependent player data and approximate per-game map
  communicate limitations rather than suggesting live or official data.

The user requested an English interface, comparison hierarchy, animated
switching and player/team views inspired by sports apps. Those requests
guided the implementation; this is not a reproduction of a third-party
rating system. Screenshots are omitted pending a review of the rights to
visible third-party images and marks.
