# Media, stores and public posts (team reference; rules in .claude/rules/team.md)

- Every filmed shot is verified from the game's own per-frame data log (subject visibility, size, occlusion, world
  loading, sound) with automatic pass/fail; failed shots are re-shot without Artem; a cut comes with a per-shot data
  report; eyes only judge taste (Artem, 13.10).
- Show Artem a cheap raw preview early and turn his notes into measurable checks; before a full batch, run 2–3 plans
  end to end (record → render → edit) in 10–15 min; one camera planner on replay data for trailer and TikTok, not
  per-plan patches; separate fixable third-party limits from workarounds early; give times only from measured rates.
- YouTube trailer (Artem, 15–18.10): staged, cinematic, English, 90 s of ~30 shots (2–4 s): real-weapon strikes, air
  defence, nuke finale; opens on cruise missiles low over a city at night; no feature captions, only the mod's own
  screens; ends on the name INCOMING as text. Only mod sounds plus music (Juggernaut, Scott Buckley, CC BY); mod
  effects real, no post VFX, slow-mo or speed ramps. Every shot at or above the reference; anything that changes the
  impression goes to Artem before it enters the film; final render only when the «не дотягивает» list is empty;
  filming on copies only.
- TikTok (Artem, 13.10, 17.10, 01.11): through a player's eyes (no tripod cameras) plus night FPV passes over the
  hottest strikes; source is Artem's own recordings; posted clips are never re-uploaded; always deliver a no-music
  version. Each post: one continuous 8–12 s shot, fire/launch/blast big in frame 0, an on-screen Russian line from
  frame 0, the mod name on screen, 3–5 s of the dust wall rolling at the camera with the hit's game sound; Artem
  picks a popular sound at upload; 3–4 posts a week; gate = 2 s retention ≥ 60 % (TikTok Studio); run the TikTok
  skill's `check.py` on the final MP4.
- TikTok caption (Artem, 15.10): one short EN line, then RU, no emoji, saying which mod this is (never describing
  what the viewer sees), ≤ 5 tags including weapon tags, a one-line CC BY music credit. Posts go on the mod's own
  account. Our MP4s and images carry Anthropic C2PA Content Credentials; we do not strip them.
- Public TikTok counters and comments need no login: page JSON `__UNIVERSAL_DATA_FOR_REHYDRATION__` via curl;
  comments via `/api/comment/list/?aid=1988&aweme_id=<id>&count=50&cursor=N` with that page's cookies and Referer.
- Store pages: an optimal mix of GIFs and stills, most interesting only; a still is never a frame of a GIF shown on
  the same pages (Artem, 29.10).
- Reddit: r/feedthebeast one own-mod showcase per week, no download links in the post (link in a comment);
  r/Minecraft English, 12 h between posts; r/ClaudeAI must explain in detail how Claude helped, karma > 100.
- Artem allows studying Photon, Complementary and Bliss shaderpack sources for techniques under his responsibility;
  no deliberate 1:1 copying (Artem, 08.11).
