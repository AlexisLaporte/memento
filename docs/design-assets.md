# Design Assets

Visual assets for the Memento landing page and app. All generated with **Adobe Firefly (Gemini Flash model)**.

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--background` | `#f2ebe0` | Warm cream background |
| `--foreground` | `#1e3a32` | Dark forest green text |
| `--primary` | `#2a5a4a` | Deep teal — buttons, links |
| `--accent` | `#c87941` | Warm orange — highlights |
| `--muted` | `#e6e0d6` | Light beige — muted backgrounds |
| `--muted-foreground` | `#6a7a6e` | Sage green — secondary text |
| `--card` | `#faf7f2` | Off-white cards |

## Fonts

- **Headings**: Alice (serif) — `@fontsource/alice`
- **Body**: Geist Variable (sans) — `@fontsource-variable/geist`

## Logo

| File | Source | Prompt |
|------|--------|--------|
| `logo-book.svg` | Firefly → potrace | "un logo (uniquement un logo sans rien d'autres) qui mélange un M et le concept d'un livre" |
| `logo-book.png` | Firefly (trimmed) | idem |
| `favicon.ico` / `favicon-32.png` / `apple-touch-icon.png` | Derived from logo-book.png | — |

## Illustrations

All in `frontend/public/`. Style: flat illustration, office/bureau, plants, teal/green/orange warm tones.

| File | Firefly Prompt | Used in |
|------|---------------|---------|
| `illust-collab.png` | "des gens qui travaillent ensemble sur un bureau en relisant un document, diversité" | Hero background |
| `illust-code.png` | "un écran d'ordinateur affichant du code markdown avec un arbre de fichiers sur le côté, bureau avec plantes, style illustration flat" | Feature: GitHub-native |
| `illust-access.png` | "une personne qui distribue des badges d'accès à une équipe diverse dans un bureau moderne" | Feature: Access control |
| `illust-startup.png` | "une startup avec 3 personnes autour d'un écran montrant de la documentation, diversité" | Feature: AI/MCP |
| `illust-aerial.png` | "vue aérienne d'un bureau avec plusieurs laptops ouverts sur de la documentation, tasses de café" | CTA section |
| `hero-library.png` | "un focus sur la librairie avec plein de documents" | Available (unused) |
| `hero-team.png` | "plusieurs personnes qui travaillent" | Available (unused) |
| `illust-review.png` | "plusieurs personnes qui font un bilan" | Available (unused) |

## Generating new illustrations

Use Adobe Firefly with the **Gemini Flash** model. Key prompt patterns for consistency:

- Always include: "style illustration flat, palette teal et orange/beige"
- Include "plantes" and "bureau moderne" for office scenes
- Include "diversité" for people scenes
- Keep prompts in French (Firefly handles it well)
