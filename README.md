# claude-code-video-toolkit

[![GitHub release](https://img.shields.io/github/v/release/digitalsamba/claude-code-video-toolkit)](https://github.com/digitalsamba/claude-code-video-toolkit/releases)

An AI-native video production workspace for [Claude Code](https://claude.ai/code). Create professional videos with AI assistance — from concept to final render.

## A Note from the Author *(not AI-generated)*

> I've spent months painstakingly putting this toolkit together and plan to keep iterating on it. AI makes things easier, but hard work still has huge value. Every video I create is a chance for improvement — every skill, template, tool, and workflow here has been refined through that cycle. It would be wonderful if others wanted to get involved with that: use it, refine it, and feed back into the repo via an issue or PR what you learn.
>
> My own use case is fairly specific: creating sprint review videos for the AI mobile development arm of [Digital Samba](https://www.digitalsamba.com/). But the idea behind this project is a reusable toolkit for using Claude Code to autonomously generate any kind of "explainer" style video — product demos, walkthroughs, presentations, whatever you need. Autonomous video creation is a lofty ideal for such a subjective field, but we can try :)
>
> What makes this work is that Claude Code is fantastically resourceful and flexible — give it the framing and tooling that this toolkit provides and it will adapt it to create templates and videos based on your prompting. The skills, templates, and tools here are building blocks. Claude Code is the builder. You are the director, editor, and designer.
>
> **If you're getting started**, I'd suggest beginning with the `/template` command and working through creating a template for your own use case.
>
> **I highly recommend a [RunPod](https://runpod.io/) account** for running open-source models with GPU resources. It's cheap — typically pennies per job, and rarely more than $10/month even with heavy use. I will likely make Qwen3-TTS the default for voiceovers as it arguably produces better results with significantly less effort and cost than ElevenLabs.
>
> **Free Docker images** — I've made all the RunPod images I use in this project available publicly:
> - `ghcr.io/conalmullan/video-toolkit-qwen-edit` — AI image editing (Qwen-Image-Edit)
> - `ghcr.io/conalmullan/video-toolkit-realesrgan` — AI image upscaling (Real-ESRGAN)
> - `ghcr.io/conalmullan/video-toolkit-propainter` — Video watermark removal (ProPainter)
> - `ghcr.io/conalmullan/video-toolkit-sadtalker` — Talking head generation (SadTalker)
> - `ghcr.io/conalmullan/video-toolkit-qwen3-tts` — Text-to-speech (Qwen3-TTS)
> - `ghcr.io/conalmullan/video-toolkit-flux2` — Text-to-image & editing (FLUX.2 Klein 4B)
> - `ghcr.io/conalmullan/video-toolkit-acestep` — AI music generation (ACE-Step 1.5)
>
> My motto: **Be brave. Experiment.** And please share any videos you create or ideas you have back with the project — it helps me keep improving this toolkit for everyone.

## What is this?

This toolkit gives Claude Code the knowledge and tools to help you create videos:

- **Skills** — Domain expertise in Remotion, ElevenLabs, FFmpeg, Playwright
- **Commands** — Guided workflows like `/video`, `/record-demo`, `/contribute`
- **Templates** — Ready-to-customize video structures
- **Brands** — Visual identity profiles (colors, fonts, voice settings)
- **Tools** — Python CLI for audio generation

Clone this repo, open it in Claude Code, and start creating videos.

## Quick Start

### Prerequisites

| Requirement | Status | Purpose |
|-------------|--------|---------|
| [Node.js](https://nodejs.org/) 18+ | **Required** | Renders videos with Remotion |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | **Required** | AI assistant for video creation |
| [Python](https://python.org/) 3.9+ | Optional | AI voiceover, audio tools |
| [FFmpeg](https://ffmpeg.org/) | Optional | Media conversion |
| [RunPod account](https://runpod.io/) | Optional | Cloud GPU (TTS, image editing, music gen) |
| [ElevenLabs API key](https://elevenlabs.io/) | Optional | Premium AI voices |

### Try It Now

```bash
git clone https://github.com/digitalsamba/claude-code-video-toolkit.git
cd claude-code-video-toolkit/examples/hello-world
npm install
npm run render    # Outputs MP4 — no API keys needed
```

### Full Setup

```bash
# Clone the toolkit
git clone https://github.com/digitalsamba/claude-code-video-toolkit.git
cd claude-code-video-toolkit

# Set up environment (all keys are optional)
cp .env.example .env

# Install Python dependencies (optional — only needed for AI tools)
python -m venv .venv
source .venv/bin/activate
pip install -r tools/requirements.txt

# Start Claude Code
claude
```

### Create Your First Video

In Claude Code, run:

```
/video
```

This will:
1. Scan for existing projects (resume or create new)
2. Choose template (sprint-review, product-demo)
3. Choose brand (or create one with `/brand`)
4. Plan scenes interactively
5. Create project with VOICEOVER-SCRIPT.md

**Multi-session support:** Projects span multiple sessions. Run `/video` to resume where you left off.

Then iterate with Claude Code to record demos, refine content, and render.

## Features

### Skills

Claude Code has deep knowledge in:

| Skill | Description |
|-------|-------------|
| **remotion** | React-based video framework — compositions, animations, rendering |
| **elevenlabs** | AI audio — text-to-speech, voice cloning, music, sound effects |
| **ffmpeg** | Media processing — format conversion, compression, resizing |
| **playwright-recording** | Browser automation — record demos as video |
| **frontend-design** | Visual design refinement for distinctive, production-grade aesthetics |
| **qwen-edit** | AI image editing — prompting patterns and best practices |
| **acestep** | AI music generation — prompts, lyrics, scene presets, video integration |
| **runpod** | Cloud GPU — setup, Docker images, endpoint management, costs |

### Commands

| Command | Description |
|---------|-------------|
| `/video` | Video projects — list, resume, or create new |
| `/scene-review` | Scene-by-scene review in Remotion Studio |
| `/design` | Focused design refinement session for a scene |
| `/brand` | Brand profiles — list, edit, or create new |
| `/template` | List available templates or create new ones |
| `/skills` | List installed skills or create new ones |
| `/contribute` | Share improvements — issues, PRs, examples |
| `/record-demo` | Record browser interactions with Playwright |
| `/generate-voiceover` | Generate AI voiceover from a script |
| `/redub` | Redub existing video with a different voice |
| `/voice-clone` | Record, test, and save a cloned voice to a brand |
| `/versions` | Check dependency versions and toolkit updates |

> **Note:** After creating or modifying commands/skills, restart Claude Code to load changes.

### Templates

Pre-built video structures in `templates/`:

- **sprint-review** — Sprint review videos with demos, stats, and voiceover
- **sprint-review-v2** — Composable scene-based sprint review with modular architecture
- **product-demo** — Marketing videos with dark tech aesthetic, stats, CTA

See `examples/` for finished projects you can learn from (oldest first, showing toolkit evolution):

| Date | Demo | Description |
|------|------|-------------|
| 2025-12-05 | [sprint-review-cho-oyu](https://demos.digitalsamba.com/sprint-review-cho-oyu.mp4) | iOS sprint review with demos |
| 2025-12-10 | [digital-samba-skill-demo](https://demos.digitalsamba.com/video/digital-samba-skill-demo.mp4) | Product demo showcasing Claude Code skill |
| 2026-01-22 | [ds-remote-mcp](https://demos.digitalsamba.com/video/ds-remote-mcp.mp4) | Remote MCP server demo *(the jazz background music is a joke)* |
| 2026-01-25 | [schlumbergera](https://demos.digitalsamba.com/video/schlumbergera.mp4) | Android sprint review video |
| 2026-02-23 | [cortina](https://demos.digitalsamba.com/video/sprint-review.mp4) | Mobile platforms sprint review |
| 2026-03-15 | [the-space-between](https://demos.digitalsamba.com/video/the-space-between.mp4) | AI-generated video essay — flux2 avatar, Qwen3-TTS voice, SadTalker animation |

### Scene Transitions

The toolkit includes a transitions library for scene-to-scene effects:

| Transition | Description |
|------------|-------------|
| `glitch()` | Digital distortion with RGB shift |
| `rgbSplit()` | Chromatic aberration effect |
| `zoomBlur()` | Radial motion blur |
| `lightLeak()` | Cinematic lens flare |
| `clockWipe()` | Radial sweep reveal |
| `pixelate()` | Digital mosaic dissolution |
| `checkerboard()` | Grid-based reveal (9 patterns) |

Plus official Remotion transitions: `slide()`, `fade()`, `wipe()`, `flip()`

Preview all transitions:
```bash
cd showcase/transitions && npm install && npm run studio
```

See [lib/transitions/README.md](lib/transitions/README.md) for full documentation.

### Brand Profiles

Define visual identity in `brands/`. When you create a project with `/video`, the brand's colors, fonts, and styling are automatically applied.

```
brands/my-brand/
├── brand.json    # Colors, fonts, typography
├── voice.json    # ElevenLabs voice settings
└── assets/       # Logo, backgrounds
```

Included brands: `default`, `digital-samba`

Create your own with `/brand`.

### Project Management System

Video projects are tracked through a multi-session lifecycle:

```
planning → assets → review → audio → editing → rendering → complete
```

Each project has a `project.json` that tracks:
- **Scenes** — What to show, asset status, visual types
- **Audio** — Voiceover and music status
- **Sessions** — Work history across Claude Code sessions
- **Phase** — Current stage in the workflow

The system automatically reconciles intent (what you planned) with reality (what files exist), and generates a `CLAUDE.md` per project for instant context when resuming.

See [lib/project/README.md](lib/project/README.md) for schema details, scene status tracking, and filesystem reconciliation logic.

### Python Tools

Audio, video, and image tools in `tools/`:

```bash
# Generate voiceover (ElevenLabs)
python tools/voiceover.py --script script.md --output voiceover.mp3

# Generate voiceover (Qwen3-TTS — self-hosted, cheaper alternative)
python tools/voiceover.py --provider qwen3 --speaker Ryan --scene-dir public/audio/scenes --json
python tools/qwen3_tts.py --text "Hello world" --tone warm --output hello.mp3

# Generate background music (ElevenLabs)
python tools/music.py --prompt "Upbeat corporate" --duration 120 --output music.mp3

# Generate background music (ACE-Step — free, precise BPM/key control)
python tools/music_gen.py --preset corporate-bg --duration 120 --output music.mp3
python tools/music_gen.py --prompt "Dramatic cinematic" --duration 30 --bpm 90 --key "D Minor" --output reveal.mp3

# Generate sound effects
python tools/sfx.py --preset whoosh --output sfx.mp3

# Redub video with different voice
python tools/redub.py --input video.mp4 --voice-id VOICE_ID --output dubbed.mp4

# Add background music to existing video
python tools/addmusic.py --input video.mp4 --prompt "Subtle ambient" --output output.mp4

# Rebrand NotebookLM videos (trim outro, add your logo/URL)
python tools/notebooklm_brand.py --input video.mp4 --logo logo.png --url "mysite.com" --output branded.mp4

# AI image editing (style transfer, backgrounds, custom prompts)
python tools/image_edit.py --input photo.jpg --style cyberpunk
python tools/image_edit.py --input photo.jpg --prompt "Add sunglasses"

# AI image upscaling (2x/4x)
python tools/upscale.py --input photo.jpg --output photo_4x.png --runpod

# Remove watermarks (requires RunPod or NVIDIA GPU)
python tools/dewatermark.py --input video.mp4 --preset sora --output clean.mp4 --runpod

# Locate watermark coordinates
python tools/locate_watermark.py --input video.mp4 --grid --output-dir ./review/

# Generate talking head video from image + audio (SadTalker)
# Creates animated presenter/narrator from a static portrait + voiceover audio
# Use with NarratorPiP component for picture-in-picture presenter overlays
python tools/sadtalker.py --image portrait.png --audio voiceover.mp3 --output talking.mp4

# AI image generation (FLUX.2 Klein 4B — text-to-image + editing)
python tools/flux2.py --prompt "A sunset over mountains"
python tools/flux2.py --preset title-bg --brand digital-samba
python tools/flux2.py --input photo.jpg --prompt "Add sunglasses"
python tools/flux2.py --list-presets
```

**Tool Categories:**

| Type | Tools | Purpose |
|------|-------|---------|
| **Project** | voiceover, music, music_gen, sfx | Used during video creation workflow |
| **Utility** | redub, addmusic, notebooklm_brand, locate_watermark | Quick transformations, no project needed |
| **Cloud GPU** | image_edit, upscale, dewatermark, sadtalker, qwen3_tts, flux2, music_gen | AI processing via RunPod (see below) |

See [docs/runpod-setup.md](docs/runpod-setup.md) for Cloud GPU tool setup.

### Pre-built Docker Images

Cloud GPU tools use pre-built Docker images deployed to RunPod serverless:

| Tool | Docker Image | GPU |
|------|--------------|-----|
| image_edit | `ghcr.io/conalmullan/video-toolkit-qwen-edit:latest` | 48GB+ (A6000, L40S) |
| upscale | `ghcr.io/conalmullan/video-toolkit-realesrgan:latest` | 24GB (RTX 3090/4090) |
| dewatermark | `ghcr.io/conalmullan/video-toolkit-propainter:latest` | 24GB (RTX 3090/4090) |
| sadtalker | `ghcr.io/conalmullan/video-toolkit-sadtalker:latest` | 24GB (RTX 4090) |
| qwen3_tts | `ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest` | 24GB (ADA) |
| flux2 | `ghcr.io/conalmullan/video-toolkit-flux2:latest` | 24GB (ADA) |
| music_gen | `ghcr.io/conalmullan/video-toolkit-acestep:latest` | 24GB+ (AMPERE/ADA) |

Dockerfiles and handlers are in `docker/`. Run `python tools/<tool>.py --setup` to auto-deploy.

**Cost:** RunPod is pay-per-second with no minimums. Typical usage is ~$0.01-0.15 per job. Even with heavy experimenting, expect to spend less than $10/month.

## Project Structure

```
claude-code-video-toolkit/
├── .claude/
│   ├── skills/          # Domain knowledge for Claude
│   └── commands/        # Slash commands (/video, /brand, etc.)
├── lib/                 # Shared components, theme system, utilities
│   ├── components/      # Reusable video components (11 components)
│   ├── transitions/     # Scene transition effects (7 custom + 4 official)
│   ├── theme/           # ThemeProvider, useTheme
│   └── project/         # Multi-session project system
├── tools/               # Python CLI tools
├── templates/           # Video templates
├── brands/              # Brand profiles
├── projects/            # Your video projects (gitignored)
├── examples/            # Curated showcase projects with finished videos
├── assets/              # Shared assets
├── playwright/          # Recording infrastructure
├── docs/                # Documentation
└── _internal/           # Toolkit metadata & roadmap
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Creating Templates](docs/creating-templates.md)
- [Creating Brands](docs/creating-brands.md)
- [Project System](lib/project/README.md) — Multi-session lifecycle, schema, reconciliation
- [Optional Components](docs/optional-components.md) — GPU tools setup (dewatermark)
- [RunPod Setup](docs/runpod-setup.md) — Cloud GPU configuration
- [Toolkit Development](_internal/ROADMAP.md) — Roadmap, backlog, changelog for the toolkit itself

## Video Workflow

```
/video → Script → Assets → Scene Review → Design → Audio → Preview → Render
```

1. **Create project** — Run `/video`, choose template and brand
2. **Review script** — Edit `VOICEOVER-SCRIPT.md` to plan content and assets
3. **Gather assets** — Record demos with `/record-demo` or add external videos
4. **Scene review** — Run `/scene-review` to verify visuals in Remotion Studio
5. **Design refinement** — Use `/design` to improve slide visuals with the frontend-design skill
6. **Generate audio** — AI voiceover with `/generate-voiceover`
7. **Configure** — Update config file with asset paths and timing
8. **Preview** — `npm run studio` for live preview
9. **Iterate** — Work with Claude Code to adjust timing, styling, content
10. **Render** — `npm run render` for final MP4

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Built for use with [Claude Code](https://claude.ai/code) by Anthropic.
