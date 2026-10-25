# NJ Dream Home Carousel Agent

Daily Instagram carousels for Therm The Realtor (@therm.realtor), NJ Dream Home, eXp Realty.

- `PLAYBOOK.md`: the rules the agent follows (topics, hooks, accuracy, compliance, posting times, approval).
- `render_carousel.py`: renders a carousel from a JSON spec in the NJ Dream Home template.
- `scenes.py`: original illustrated scenes for local place cards.
- `make_stories.py`: 9:16 Instagram Story frames from a carousel.
- `make_reel.py`: the silent 9:16 Reel version of a carousel; the Brain's trending Instagram audio is attached at scheduling.
- `formats.py`: the three carousel jobs (story, bold, proof); see .claude/skills/carousel-formats/SKILL.md.
- `tools/shoot.py` + workflow "Screenshot official pages": real screenshots of official pages for bold step slides.
- `make_sheet.py`: one-image preview of all six slides.
- `specs/`: one JSON spec per post. `posts/`: rendered images, served to Metricool from this public repo.

Nothing posts without Therm's approval.
