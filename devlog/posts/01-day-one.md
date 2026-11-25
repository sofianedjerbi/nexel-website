title: Day one: a world for robots, then a game
date: 2026-11-08
image: island.png
summary: It started as a server for AI players. By the evening it had to be a game people want to play.
---
Nexel Worlds started on 8 November as something else: a persistent world where the players are AI agents running on a local model. The first version was a server, a world of chunks saved in SQLite, and eight scripted bots walking, digging and building. It worked, and it was fast.

Then it had to be looked at, and the first look was a debug viewer. The verdict was short: ugly, and nobody could tell how to play. Then: still ugly, and the latency is insane.

## What we fixed that day

- **Latency.** A one-tick step took two ticks (400 ms), and the page waited for the server before moving you. Now your character moves the moment you press a key and the server confirms within a tick.
- **The look.** Hand-drawn tiles at uneven scales made a checkerboard. We switched to the Sprout Lands art pack, drawn at whole-number zooms only, so pixels stay square.
- **Letters.** No font we tried felt right, so the game got its own: a 5 by 7 pixel font, drawn letter by letter. It is the one you are reading.
- **Feel.** Collisions you could trust, things that spawned everywhere, animation for every action.

![The first screen's island, as it looks today](img/island.png)
