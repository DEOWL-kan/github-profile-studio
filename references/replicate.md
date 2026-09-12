# Path A — "make mine look like theirs"

Read this when the user points at a profile they like (a handle, a link, or a screenshot) and wants something similar for themselves.

## What "like theirs" usually means

Ask, or show two readings side by side, because it varies. It can mean:
- the **layout**: hero card, centred header, two columns, a sections order;
- the **look**: palette, typography, terminal or retro styling, animation;
- the **widgets**: stats cards, snake, typing header, badges;
- the **tone**: minimal and quiet vs playful and dense.

What it never means is copying the person. Their name, photo, logo, words, projects and numbers stay theirs; every value on the user's page is the user's own.

## Steps

1. **Take it apart.**

   ```bash
   python3 "$SKILL_DIR/scripts/inspect_profile.py" THEIR_LOGIN        # or ORG --org
   ```

   This prints the licence, layout features (tables, `<details>`, centred blocks, theme-aware `<picture>`), every image classified as a live service, a workflow-generated file, or a static file, the workflows with their schedules and actions, and the repo's asset files.

2. **See it rendered.**

   ```bash
   "$CHROME" --headless=new --force-dark-mode --window-size=1280,1600 --virtual-time-budget=10000 \
     --screenshot=theirs.png https://github.com/THEIR_LOGIN
   ```

   Look at it before planning. Lazily loaded images sometimes show only as alt text in headless shots; that is the screenshot, not the page. Open the image URLs directly if you need them.

3. **Decide what may be reused.**
   - **MIT, Apache, BSD, etc.**: the code, such as a generator script, may be reused under its terms. Keep the licence notice with it.
   - **No licence** (common for profile repos): rebuild the layout and ideas with your own code. Copy no code, images or text.
   - **Third-party services** they embed (stats cards, badges): anyone can embed those. They come with the reliability notes in components.md.

4. **Map each element to the user.** Build a small table: their element → what the user will show there. Examples:
   - their commit count → the user's commit count;
   - their project grid → the user's chosen projects;
   - their anime GIF → the user's own image, or nothing.

   Mark elements with no honest equivalent (for example, a star count the user doesn't have) and suggest a replacement instead of faking it.

5. **Build**, using the matching path: the neofetch card (portrait.md), widgets (components.md), or content sections (content.md).

6. **Show a comparison.** Put their page and the user's preview side by side (`magick theirs.png ours.png +append compare.png`) so the user can judge "similar enough". Then customise from their feedback.

## If there is only a screenshot

Identify components visually: the stats-card shapes, the snake grid, typing text, badge rows and the terminal card are all recognisable. Ask for the handle if it would help, since inspect_profile.py gives certainty about how things are produced.
