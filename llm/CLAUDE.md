# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file scrollytelling explainer titled **"Comment marche un LLM ?"** — a French-language visual essay on how large language models work. The whole site is `index.html`; there is no build step, no package manager, no tests.

## Running it

Open `index.html` directly in a browser, or serve the directory with any static server (e.g. `python3 -m http.server`). React 18, ReactDOM 18, and Babel Standalone are loaded from `unpkg` via `<script>` tags with SRI hashes — the JSX inside `<script type="text/babel">` is compiled in the browser. There is intentionally no toolchain.

## Architecture

All ~2.5k lines live in one `<script type="text/babel">` block at the bottom of `index.html` (starts ~L622). Structure:

- **`App`** (L2481) renders a fixed topbar, a side "rail" of navigation ticks, the hero section, then nine act sections in order.
- **`Act1`..`Act9`** (L691, 903, 1112, 1299, 1457, 1687, 1887, 2105, 2309) are independent full-height sections, each driven by its own scroll progress. The list of act ids/names is centralized in `ACT_IDS` / `ACT_NAMES` (L2456) — keep these arrays in sync with the components rendered in `App` and with the section `id`s used inside each act.
- **Two custom hooks drive everything visual:**
  - `useScrollProgress(ref)` (L626) returns a `0..1` value representing how far the referenced section has scrolled through the viewport. Each act calls this on its own outer ref and then maps the resulting `p` to animation states.
  - `useActiveAct(actIds)` (L654) returns the index of the act currently dominant in the viewport; used to highlight the topbar pill and rail tick, and to support arrow-key navigation.
- **Animation helpers** (L684): `lerp(a,b,t)`, `clamp(v,a,b)`, and `seg(p, s, e)` — the latter remaps a global `0..1` progress to a `0..1` sub-segment between `s` and `e`. Acts are typically built as a series of `seg(p, ...)` ranges that fade/move/swap sub-elements.
- **Keyboard nav** (L2485): ↑/↓ and PageUp/PageDown jump between acts by `scrollIntoView` on `ACT_IDS[active±1]`.

## Styling conventions

CSS lives in the `<style>` block at the top of `index.html`. The theme is driven by CSS custom properties on `:root` (L34):

- Layout/text: `--bg`, `--ink`, `--muted`, `--line`, `--paper`.
- Semantic role colors used throughout the acts: `--c-system`, `--c-user`, `--c-ai`, `--c-perso`, `--c-skill`, `--c-tool`, `--c-think`, `--c-cache`, `--c-compact`. When adding a new concept that needs a recognizable color, prefer extending this palette rather than hard-coding hex values inline.

Fonts are Outfit (UI) and Fira Code (mono) from Google Fonts.

## When editing

- The content is in French — preserve language and tone when modifying copy.
- Adding a new act: append to `ACT_IDS`/`ACT_NAMES`, write `ActN()` following the existing `useRef` + `useScrollProgress` + `seg(p, ...)` pattern, and render `<ActN />` inside `App`.
- Babel Standalone is slow on large files; if iteration time becomes a problem, the right move is to migrate to a real toolchain rather than fighting the in-browser compile.
