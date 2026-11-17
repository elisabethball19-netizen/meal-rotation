# CLAUDE.md — Meal Rotation App

## Project Overview
A mobile-first, zero-decision weekly meal rotation Progressive Web App (PWA) designed for minimal cognitive load, reliable offline persistence, and eventual packaging as a native iOS and Android App Store release via Capacitor.

## Strict Architectural Constraints
- **Zero Build Tools & Zero Frameworks:** Keep the core web application 100% pure vanilla HTML, CSS, and JavaScript (`ES6+`).
- **Banned Dependencies in Core App:** Do NOT introduce React, Vue, Svelte, TypeScript, Tailwind, CSS preprocessors, Vite, Webpack, Rollup, or `npm` frontend libraries into the web app layer.
- **Modular File Structure:** Keep concerns separated cleanly across standalone files (`index.html`, `styles.css`, `import-export.js`, and modular feature scripts) rather than bloating a single monolithic file.

## Data & Persistence Rules
- **Client-Side First:** All user data lives locally on the device (`localStorage` currently, migrating to Capacitor native storage/`@capacitor/preferences` or SQLite before iOS App Store submission so iOS cannot purge data).
- **Backup Compatibility:** Preserve `version: 2` JSON backup import/export compatibility—especially ensuring file pickers work reliably on Android and iOS mobile browsers/webviews.
- **Error Resilience:** Guard all storage writes against quota/write failures without triggering infinite recovery loops.

## UI & UX Design Principles
- **Mobile-First Ergonomics:** Design for one-handed phone usage with generous tap targets, clear visual hierarchy, and zero horizontal overflow.
- **Progressive Disclosure:** Keep primary views clean, calm, and scannable. Avoid cluttered dashboards, heavy modals, or multi-step onboarding popups.

## Workflow & Editing Rules for Claude
- **Minimal Blast Radius:** When asked for a visual or interactive tweak, inspect and edit *only* the relevant file(s). Do not refactor unrelated modules unless explicitly asked.
- **Explain Before Big Changes:** For multi-file feature additions (e.g., multiple cooking timers, floating active-step anchor, Capacitor setup), briefly outline the plan and affected files before writing code.
- **Mobile PR Summaries:** Keep Pull Request descriptions concise and written in plain English so changes are easy to review on a phone screen.
