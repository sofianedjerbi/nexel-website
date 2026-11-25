title: Seen through the rock, a name, and houses block by block
date: 2026-11-15
image: old-build.jpg
summary: An x-ray view for when the land hides you, black tiles on one phone, the name Nexel Worlds, and real building.
---
## Seen through the rock

Behind a mountain or in a cave, a top-down camera loses you. So when land hides you, a window opens through it. It took many rounds: a circle round you, then a circle that also showed water, then one cut exactly to the pixel, then one painted by the same code as the land itself, so the two could never disagree.

## Black tiles on a phone

A screenshot from a phone showed black tiles along cliff tops. We could not reproduce it on the Mac, with the same world, spot and screen size. The cause was the phone's graphics chip drawing chained canvas copies wrong. The fix at the time was to stop asking the GPU: the land was painted pixel by pixel in JavaScript and uploaded once. (Today's HD look draws real blocks, and that phone is fine with it.)

## A name

The project was called Megastructure. After a long search it became **Nexel Worlds**: nexus plus the -xel of pixel, easy to say in French and English.

## Building, for real

Houses used to drop onto the world whole. Now there is a build mode: a cursor, Space to plan a piece (hold it for a row), and your character builds it, block by block. Walls took three drawings in one day. The first two looked fine on a test plot and wrong in a real player's yard. The third one was tried on that yard before we kept it.

![Build mode in the old flat look, 15 November](img/old-build.jpg)
