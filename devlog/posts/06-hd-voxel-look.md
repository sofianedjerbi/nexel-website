title: The HD voxel look
date: 2026-11-21
image: cave.png
summary: From flat tiles to real blocks with a horizon, light and shadows. The first audit said no.
---
The world was already made of cells, so we drew them as what they are: blocks, every one of them 3D, seen from above in a tilted camera, with the pixel-art tiles on every face. Far away the world bends to a horizon with a sky that follows the hour.

## The audits

We asked a separate reviewer to play the new look and grade it, without touching code. The first verdict: "Not finished, and not good looking as a 3D world." Water read as sand, an 8-deep shaft looked 1 deep, overhangs were black boxes. Eleven faults at a glance, twelve more on a closer look. It took four audits before the reviewer was happy with depth, cuts, water and shadows.

strip: old-cave.jpg cave.png | The same idea, before and after: a cave in the flat look (17 November) and in the HD look (today).

## One renderer

For a few days both looks lived side by side, with a setting. Keeping two painters in step cost us bugs every day, so the old one went. Everyone now sees the same world.

## On a phone

The game used to load in 208 requests. Now it is 12: one script, one pack of pictures, a trimmed Python library, and a service worker so the second visit comes from the phone itself.

![The cave by night, lit by a torch](img/cave-night.png)
