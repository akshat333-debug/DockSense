# Recording Guide — do this TODAY

Everything downstream blocks on this. No video = no thresholds, no metrics, no demo,
no screenshots. Two people can shoot the whole list in ~3 hours.

## Kit

- 8–12 cardboard boxes: mix of sizes. At least 3 large, 5 small.
- 1 pallet (or a low wooden board / crate as a stand-in — label it in notes).
- 1 trolley / hand truck / office chair as equipment proxy.
- Masking tape to mark zone boundaries on the floor.
- Marker pen — write a big number on each box face (helps tracking + annotation).
- Phone on a tripod, or propped on a stack of books. **Do not hand-hold.**
  Camera motion creates fake velocity and will produce false drops.

## Camera setup

- Fixed position, does not move between takes in a session.
- Landscape, 1080p, 30fps.
- Frame must show: the floor line, the pallet, and the full height a box gets lifted to.
- Good light. Avoid backlight/windows behind the scene.
- Tape two zones on the floor and note which is which:
  - `staging` (allowed)
  - `walkway` (product forbidden)

## Session protocol

Record in **sessions**. A session = one camera position, unbroken.
Name every file `S{session}_{behaviour}_{take}.mp4` — e.g. `S1_drop_03.mp4`.

Session naming matters: the train/val/test split is **by session**, not by clip.
Two takes of the same drop from the same camera position must never end up on
opposite sides of the split. Recording in labelled sessions is what makes an
honest split possible later.

Shoot **at least 3 sessions** from different camera positions:

| Session | Camera | Purpose |
|---|---|---|
| S1 | Near, side-on, ~3m | Primary tuning data |
| S2 | Far, side-on, ~6m | Scale robustness |
| S3 | Elevated / angled ~30° | **Held out. Never tune on this.** |

S3 is the honesty artifact. Tuning on S1/S2 and reporting on S3 is the difference
between a real number and a number a judge will dismantle.

## Shot list

Per behaviour, per session: **3 takes minimum**. Vary speed and box size between takes.

| # | Behaviour | What to do |
|---|---|---|
| B01 | Drop | Lift box to chest height, release cleanly, let it hit floor |
| B02 | Throw | Toss box sideways 1–2m onto floor or pallet |
| B03 | Drag | Push/pull box along floor 2m+ without lifting |
| B04 | Rough handling | Slam box down hard onto pallet; shove box into another |
| B05 | Improper stack | Place a large box on top of a small one |
| B06 | Unstable stack | Stack boxes with big overhang / visible lean |
| B07 | Zone violation | Place box in the taped `walkway` zone, leave it 5s+ |
| B08 | Pallet overhang | Place box so half of it hangs off the pallet edge |
| B09 | Stepping on box | Step on a box, hold foot there 2s+ |
| B10 | Manual heavy lift | Carry the largest box alone, no trolley in frame |
| B11 | Unsafe sequence | Lift heavy box, move, place unstably — trolley visible but unused |
| B12 | Unsafe surface | Move box through the taped `walkway`/unsafe zone |

## Hard negatives — do not skip these

**This is the most-skipped and highest-value part of the shoot.** Without them
every detector looks perfect because it never gets a chance to be wrong. These
clips are what your false-positive rate is measured on.

Record **5+ takes each**:

| Clip | Why it matters |
|---|---|
| Gentle controlled placement | Must NOT fire drop |
| Carrying a box at knee height | Must NOT fire drag |
| Box moved on a trolley | Must NOT fire drag or manual-handling |
| Correct stack, small on large | Must NOT fire improper stack |
| Person walking past a box, no contact | Must NOT fire stepping |
| Box fully on pallet, well aligned | Must NOT fire overhang |
| Person briefly crossing the walkway zone | Must NOT fire zone violation (transient) |
| Static scene, boxes at rest, 30s | Must produce ZERO incidents |

That last one is the single best demo asset you will record. "Here is 30 seconds
of normal operation and the system stayed silent" answers the question every
judge is privately asking.

## While filming — keep a notes file

For every take, one line in `data/raw/takes.csv`:

```
filename,session,behaviour,approx_start_s,approx_end_s,notes
S1_drop_01.mp4,S1,drop,2.4,3.1,large box chest height
S1_normal_01.mp4,S1,none,,,gentle placement
```

Writing rough timestamps at record time takes seconds. Reconstructing them later
from footage takes hours, and it is the input to every metric you report.

## Done when

- [ ] 3 sessions, different camera positions
- [ ] 12 behaviours × 3 takes × 2 sessions (S3 can be thinner)
- [ ] 8 hard-negative categories, 5 takes each
- [ ] One 30s+ fully-normal clip
- [ ] `takes.csv` filled in
- [ ] Files copied to `data/raw/`
