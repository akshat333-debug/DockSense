# HandleGuard AI — Complete Project Implementation Master Plan

> **Project:** AI Video Intelligence for Warehouse Handling  
> **Working Name:** HandleGuard AI  
> **Primary Goal:** Build an AI-powered warehouse field-intelligence assistant that converts warehouse video into explainable, actionable, preventive operational intelligence.  
> **Submission Goal:** A working prototype that demonstrates video ingestion, object detection/tracking, behaviour identification, risk classification, incident visualization, AI-generated explanations/recommendations, and at least **10 predefined behaviours/scenarios**.  
> **Core Principle:** Do not build a CCTV analytics demo. Build a **damage-prevention decision system**.

---

# 0. Executive Definition

HandleGuard AI must observe loading/unloading operations from CCTV, recorded video, or smartphone footage and reason over **sequences of actions**, not just single frames.

The complete pipeline should be:

```text
Camera / Video
    ↓
Frame decoding + preprocessing
    ↓
Object detection
    ↓
Multi-object tracking
    ↓
Pose / spatial / scene understanding
    ↓
Temporal event extraction
    ↓
Behaviour reasoning
    ↓
Risk scoring
    ↓
Incident creation
    ↓
Evidence clip + explanation
    ↓
Alert / supervisor review
    ↓
Corrective action
    ↓
Feedback + analytics + learning
```

The project is successful only if a reviewer can answer all of the following:

1. What exactly happened?
2. Which product/object/person/equipment was involved?
3. Where did it happen?
4. When did it happen?
5. Why was the event considered risky?
6. What evidence supports that conclusion?
7. How confident is the system?
8. What corrective action is recommended?
9. Can a supervisor replay the evidence?
10. Can the system summarize trends across a shift?
11. Can a supervisor query incidents conversationally?
12. Can false positives be reviewed and corrected?
13. Can the system operate without identifying employees?
14. Can the system demonstrate at least 10 required behaviours?
15. Can the team report measurable AI, operational, business, and human-impact metrics?

---

# 1. Product Scope Lock

## 1.1 In-scope for the submission

The prototype must include:

- Recorded video upload.
- Optional live webcam / RTSP input if time permits.
- Warehouse-scene object detection.
- Person/product/pallet/equipment tracking.
- At least 10 behaviour/scenario detectors.
- Temporal reasoning across multiple frames.
- Damage-risk classification.
- Risk score from 0–100.
- Confidence score separate from risk score.
- Incident timestamp.
- Bounding-box/track evidence.
- Automatic short incident replay clip.
- Human-readable explanation.
- Recommended corrective action.
- Dashboard.
- Event timeline.
- Filters by behaviour, risk, date/time, loading bay, review status.
- Shift-level statistics.
- AI supervisor assistant grounded only in stored incidents and approved SOP rules.
- Review workflow:
  - Confirm incident.
  - Mark false positive.
  - Add supervisor note.
  - Change severity if required.
- Privacy controls.
- Exportable incident report.
- Evaluation metrics.
- Demo scenarios.
- Submission-ready architecture and screenshots.

## 1.2 Out of scope for the first submission

Do not spend critical development time on:

- Face recognition.
- Worker identity tracking.
- Employee ranking.
- Automated punitive decisions.
- Full warehouse digital twin.
- Production-grade multi-site deployment.
- Complex reinforcement learning.
- Full WMS/ERP integration.
- Expensive cloud-scale streaming architecture.
- Custom foundation-model training from scratch.
- Guaranteed physical-damage diagnosis from video alone.
- Claims that a risky event proves actual product damage.

These can appear as future-work items.

---

# 2. Definition of “Complete”

The project should not be declared complete because the UI loads or a YOLO model draws boxes.

A complete prototype requires all layers below:

| Layer | Must be complete |
|---|---|
| Product definition | Yes |
| Behaviour taxonomy | Yes |
| Dataset plan | Yes |
| Annotation format | Yes |
| Video ingestion | Yes |
| Object detection | Yes |
| Tracking | Yes |
| Temporal features | Yes |
| Behaviour rules/models | Yes |
| Risk scoring | Yes |
| Incident engine | Yes |
| Evidence clips | Yes |
| Dashboard | Yes |
| AI assistant | Yes |
| Human review | Yes |
| Database | Yes |
| API | Yes |
| Metrics | Yes |
| Tests | Yes |
| Privacy controls | Yes |
| Demo | Yes |
| Presentation evidence | Yes |
| User feedback | Yes |
| Documentation | Yes |

---

# 3. Behaviour Taxonomy

Implement **at least 10** behaviours. Prefer 12 so that the team has redundancy if one detector performs poorly.

## 3.1 Mandatory target behaviours

### B01 — Product Dropped

**Definition:** A product leaves controlled support, undergoes rapid downward motion, and comes into contact with the floor/pallet/another product with an abrupt velocity change.

**Evidence required:**
- Product track ID.
- Product center trajectory.
- Estimated vertical displacement.
- Estimated fall duration.
- Approximate drop height or image-space drop magnitude.
- Impact moment.
- Post-impact state.

**Possible signals:**
- Large downward change in center-y.
- Increasing vertical velocity.
- Sudden stop.
- Bounding box overlaps floor region.
- Product remains stationary after impact.

**Do not classify when:**
- Detection jitter is responsible.
- Product is intentionally lowered gently.
- Camera movement causes apparent motion.

**Risk modifiers:**
- Drop height.
- Product class.
- Fragility.
- Repeated drops.
- Approximate impact speed.

---

### B02 — Product Thrown

**Definition:** Product exhibits high horizontal or diagonal velocity after leaving a handler’s hand and travels unsupported before landing.

**Evidence:**
- Person-product association.
- Product track.
- Unsupported phase.
- High velocity.
- Landing/impact event.

**Difference from dropping:**
- Throwing contains significant horizontal velocity and intentional release trajectory.

---

### B03 — Product Dragged

**Definition:** Product remains in sustained contact with the floor while translating horizontally over a meaningful distance.

**Signals:**
- Bottom edge of object remains close to floor line.
- Product moves horizontally.
- Little/no vertical lift.
- Sustained duration > configurable threshold.

**Recommended corrective action:**
Use trolley, pallet truck, or suitable material-handling equipment.

---

### B04 — Rough Handling / Excessive Impact

**Definition:** A product experiences sudden high-speed motion, abrupt direction change, collision, or forceful placement.

**Possible signals:**
- Track acceleration spike.
- Collision with pallet/product/floor.
- Rapid deceleration.
- Repeated impact-like motion.

**Important:** Call it “potential rough handling” unless evidence is strong.

---

### B05 — Heavy / Large Product Placed on Smaller / Lighter Product

**Definition:** Stacking order violates size/weight hierarchy.

**Required information:**
- Product classes.
- Size proxy from bounding box / known product metadata.
- Stack relation.

**Logic example:**
```text
if item_A is vertically above item_B
and overlap_x(item_A, item_B) > threshold
and weight_A > weight_B * ratio:
    flag improper_stack
```

When real weights are unavailable, label logic as a **size-based proxy**.

---

### B06 — Unstable Stack

**Definition:** Stack geometry presents high fall/slip risk.

**Signals:**
- Excessive overhang.
- Poor horizontal overlap between tiers.
- Lean angle.
- Base narrower than upper layer.
- Large center-of-mass proxy outside support region.

**Simple stability proxy:**
```text
support_ratio = horizontal_overlap(child_box, support_box) / width(child_box)
```

Risk increases as support ratio decreases.

---

### B07 — Product Outside Designated Zone

**Definition:** Product or pallet is placed in a polygonal forbidden/non-designated region.

**Implementation:**
- Allow admin to draw zones on a reference frame.
- Store polygon coordinates.
- Calculate object centroid / footprint intersection.
- Trigger if track remains in invalid zone beyond duration threshold.

---

### B08 — Incorrect Pallet Support / Pallet Overhang

**Definition:** Product footprint is insufficiently supported by pallet or extends excessively beyond pallet boundaries.

**Signals:**
- Product bottom footprint.
- Pallet top footprint.
- Overhang ratio.
- Persistence.

**Metric:**
```text
support_fraction = area(product ∩ pallet) / area(product)
```

---

### B09 — Stepping / Standing on Product

**Definition:** Person foot/ankle region is spatially over a carton/product while the body remains supported above it for a threshold duration.

**Preferred approach:**
- Human pose estimation.
- Foot keypoints.
- Product bounding boxes.
- Contact geometry.

**Fallback approach:**
- Person bottom-center overlaps product upper region.

---

### B10 — Improper Manual Handling of Large Product

**Definition:** A large/heavy item is manually handled when team lifting or mechanical assistance is required.

**Signals:**
- Large product class.
- Only one human associated.
- No trolley/forklift/pallet jack nearby.
- Lifting/movement sequence detected.

**Important:** This is a process-risk heuristic, not proof of unsafe biomechanics.

---

### B11 — Unsafe Loading / Unloading Sequence

**Definition:** Events happen in an order that violates configured SOP sequence.

**Example state machine:**
```text
EXPECTED:
stage product
→ bring approved equipment
→ lift
→ move
→ place
→ verify stability

VIOLATION EXAMPLE:
lift/move heavy product
without equipment
→ unstable placement
```

**Implementation:**
Use a finite-state machine or event graph.

---

### B12 — Wet Floor / Unsafe Surface Handling

**Definition:** Product movement occurs in a configured wet-floor/unsafe-floor zone.

**Prototype-friendly implementation:**
- Manually label unsafe zone in demo.
- Detect product movement through unsafe zone.
- Optional segmentation model later.

---

# 4. Behaviour Configuration File

Do not hard-code all thresholds inside Python logic.

Create:

```text
configs/behaviours.yaml
```

Example:

```yaml
drop:
  enabled: true
  min_fall_pixels: 45
  min_downward_velocity: 80
  impact_deceleration: 120
  cooldown_seconds: 4
  base_risk: 70

drag:
  enabled: true
  min_distance_pixels: 100
  max_vertical_variation: 25
  min_duration_seconds: 1.5
  base_risk: 50

zone_violation:
  enabled: true
  min_duration_seconds: 2.0
  base_risk: 45
```

Also create:

```text
configs/products.yaml
configs/zones.yaml
configs/risk_weights.yaml
configs/sop_rules.yaml
```

---

# 5. System Architecture

## 5.1 Recommended architecture

```text
┌────────────────────────────┐
│ Video Sources              │
│ Upload / Webcam / RTSP     │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Video Ingestion Service    │
│ Decode / FPS / timestamps  │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Perception Layer           │
│ Detection / Pose / Zones   │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Tracking Layer             │
│ Persistent object IDs      │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Temporal Feature Engine    │
│ Trajectory / velocity /    │
│ acceleration / relations   │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Temporal Event Graph       │
│ entities + interactions    │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Behaviour Intelligence     │
│ rules + action model       │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Risk Engine                │
│ severity + confidence      │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Incident Engine            │
│ evidence / clips / state   │
└─────────┬──────────┬───────┘
          ↓          ↓
      Database    Alert Bus
          ↓          ↓
┌────────────────────────────┐
│ Backend API                │
└──────────────┬─────────────┘
               ↓
┌────────────────────────────┐
│ Dashboard + AI Assistant   │
└────────────────────────────┘
```

---

# 6. Repository Structure

Use a clean monorepo.

```text
handleguard-ai/
│
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
│
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── dependencies/
│   │   └── middleware/
│   │
│   └── web/
│       ├── package.json
│       ├── src/
│       └── public/
│
├── handleguard/
│   ├── video/
│   │   ├── reader.py
│   │   ├── stream.py
│   │   ├── frame_sampler.py
│   │   └── clip_writer.py
│   │
│   ├── perception/
│   │   ├── detector.py
│   │   ├── pose.py
│   │   ├── scene.py
│   │   └── product_classifier.py
│   │
│   ├── tracking/
│   │   ├── tracker.py
│   │   ├── track_state.py
│   │   └── associations.py
│   │
│   ├── features/
│   │   ├── trajectory.py
│   │   ├── geometry.py
│   │   ├── velocity.py
│   │   ├── acceleration.py
│   │   └── relations.py
│   │
│   ├── events/
│   │   ├── event_graph.py
│   │   ├── states.py
│   │   └── event_buffer.py
│   │
│   ├── behaviours/
│   │   ├── base.py
│   │   ├── drop.py
│   │   ├── throw.py
│   │   ├── drag.py
│   │   ├── rough_handling.py
│   │   ├── improper_stack.py
│   │   ├── unstable_stack.py
│   │   ├── zone_violation.py
│   │   ├── pallet_overhang.py
│   │   ├── stepping.py
│   │   ├── improper_manual_handling.py
│   │   ├── unsafe_sequence.py
│   │   └── unsafe_surface.py
│   │
│   ├── risk/
│   │   ├── scorer.py
│   │   ├── calibration.py
│   │   └── thresholds.py
│   │
│   ├── incidents/
│   │   ├── manager.py
│   │   ├── deduplication.py
│   │   ├── evidence.py
│   │   └── reports.py
│   │
│   ├── assistant/
│   │   ├── prompts.py
│   │   ├── retrieval.py
│   │   ├── tools.py
│   │   ├── guardrails.py
│   │   └── service.py
│   │
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── migrations/
│   │   └── repositories/
│   │
│   ├── metrics/
│   │   ├── detection.py
│   │   ├── behaviour.py
│   │   ├── latency.py
│   │   ├── business.py
│   │   └── reports.py
│   │
│   └── privacy/
│       ├── anonymize.py
│       ├── retention.py
│       └── access.py
│
├── configs/
│   ├── behaviours.yaml
│   ├── products.yaml
│   ├── zones.yaml
│   ├── risk_weights.yaml
│   └── sop_rules.yaml
│
├── data/
│   ├── raw/
│   ├── annotated/
│   ├── processed/
│   ├── clips/
│   └── sample/
│
├── models/
│   ├── detector/
│   ├── action/
│   └── pose/
│
├── scripts/
│   ├── prepare_dataset.py
│   ├── split_dataset.py
│   ├── train_detector.py
│   ├── evaluate_detector.py
│   ├── evaluate_behaviours.py
│   ├── run_video.py
│   └── seed_demo.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
│
├── notebooks/
│   ├── dataset_audit.ipynb
│   ├── threshold_tuning.ipynb
│   └── evaluation.ipynb
│
├── docs/
│   ├── architecture.md
│   ├── behaviour_taxonomy.md
│   ├── risk_model.md
│   ├── privacy.md
│   ├── API.md
│   ├── demo_script.md
│   └── submission_checklist.md
│
└── artifacts/
    ├── figures/
    ├── evaluation/
    ├── screenshots/
    └── reports/
```

---

# 7. Technology Stack

## Backend
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLite for prototype
- PostgreSQL optional for deployment

## Computer Vision
- OpenCV
- Ultralytics YOLO family or equivalent detector
- ByteTrack / BoT-SORT for tracking
- Optional pose model
- NumPy
- SciPy
- Shapely for geometric relationships

## ML
- PyTorch
- scikit-learn
- Optional LightGBM/XGBoost for risk calibration
- Optional small temporal model for action recognition

## Frontend
Choose one:
- React + Vite
- Next.js

Recommended UI:
- React
- Tailwind CSS
- Recharts
- Video.js or native HTML5 video

## AI Assistant
- Any available compact LLM
- Prefer tool/function-based answers over free-form hallucination
- Structured retrieval from incident database
- Optional local model if possible

## Deployment
- Docker
- Docker Compose
- Local first
- Optional cloud demo

---

# 8. Data Plan

## 8.1 Data sources

Use:

1. Challenge-provided warehouse videos.
2. Controlled campus recordings.
3. Synthetic staged videos.
4. Publicly available warehouse/logistics videos where licensing permits.
5. Generated variations only for augmentation, not as sole evaluation evidence.

## 8.2 Controlled recording plan

Create a miniature warehouse scene:

- 6–10 cartons.
- Small/large boxes.
- Pallet or pallet substitute.
- Trolley.
- Marked safe zone.
- Marked staging zone.
- Floor line.
- Loading table / vehicle mock.
- Smartphone camera.
- Tripod/fixed mount.

Record each behaviour under:
- Near camera.
- Far camera.
- Left-to-right.
- Right-to-left.
- Different lighting.
- Different clothing.
- Different box sizes.
- Different speeds.

Minimum desirable prototype dataset:

```text
12 behaviours
× 15–25 clips each
= 180–300 positive clips

+ 100–200 normal/negative clips
```

If schedule is too tight:
- prioritize 10 behaviours,
- minimum 10 positive clips each,
- keep separate test clips.

---

# 9. Annotation Strategy

## 9.1 Object annotations

Classes:

```text
person
carton
large_carton
fragile_package
pallet
trolley
pallet_truck
forklift
vehicle
loading_dock
```

Do not invent classes with too little data.

## 9.2 Behaviour annotations

Use JSON:

```json
{
  "video_id": "drop_014",
  "events": [
    {
      "behaviour": "drop",
      "start_s": 4.20,
      "end_s": 5.75,
      "actor_track": "person_2",
      "object_track": "carton_7",
      "risk": "high"
    }
  ]
}
```

## 9.3 Dataset split

Split by **recording session**, not individual frames.

Recommended:

```text
Train: 70%
Validation: 15%
Test: 15%
```

Avoid leakage:
- Same physical event should not appear in both train and test.
- Adjacent frames from one clip must not be split across partitions.
- If one actor repeats the same event continuously, keep that sequence within one split.

---

# 10. Video Ingestion

Implement:

```python
class VideoSource:
    def open(self): ...
    def read(self): ...
    def timestamp(self): ...
    def close(self): ...
```

Support:
- MP4 upload.
- AVI/MOV if codec permits.
- Webcam.
- Optional RTSP.

Collect metadata:
- Video ID.
- Filename.
- FPS.
- Resolution.
- Duration.
- Upload timestamp.
- Loading bay.
- Camera ID.

---

# 11. Frame Processing

Do not process every frame if unnecessary.

Config:

```yaml
video:
  inference_fps: 8
  display_fps: 24
  max_resolution: [1280, 720]
```

For each frame:
1. Decode.
2. Resize.
3. Run detector.
4. Run tracker.
5. Update temporal state.
6. Update relation graph.
7. Evaluate behaviour detectors.
8. Update incidents.
9. Draw overlays.
10. Store event evidence when necessary.

---

# 12. Object Detection

## 12.1 Baseline

Start with pretrained detector.

Determine:
- Which classes already exist.
- Which warehouse-specific classes require fine-tuning.

## 12.2 Fine-tuning

If enough annotated data exists:
- Fine-tune only warehouse-relevant classes.
- Use augmentation:
  - brightness.
  - blur.
  - scale.
  - translation.
  - partial occlusion.

Avoid unrealistic aggressive augmentation.

## 12.3 Evaluation

Report:
- Precision.
- Recall.
- mAP@0.50.
- mAP@0.50:0.95.
- Per-class metrics.

---

# 13. Multi-Object Tracking

Tracking is required because behaviour is temporal.

Each `TrackState` should contain:

```python
TrackState(
    track_id,
    class_name,
    bbox,
    confidence,
    first_seen,
    last_seen,
    history,
    velocity,
    acceleration,
    zone,
    related_tracks
)
```

History entries:

```text
timestamp
bbox
center
width
height
confidence
zone
```

Tracking goals:
- Stable IDs.
- Re-identification across short occlusions.
- Reduced duplicate incidents.

---

# 14. Spatial Scene Model

Define warehouse zones.

Example:

```yaml
zones:
  staging:
    type: allowed
  loading_bay:
    type: allowed
  walkway:
    type: restricted_product
  danger_zone:
    type: restricted
```

UI should allow polygon creation from a video frame.

Store:
- Polygon.
- Zone type.
- Name.
- Camera ID.

---

# 15. Geometry Utilities

Implement:

```python
bbox_center(box)
bbox_bottom_center(box)
iou(a, b)
intersection_area(a, b)
horizontal_overlap(a, b)
vertical_gap(a, b)
point_in_polygon(point, polygon)
distance(a, b)
relative_position(a, b)
```

These utilities should be unit-tested.

---

# 16. Temporal Feature Engine

For every track calculate:

## 16.1 Position

\[
p_t = (x_t, y_t)
\]

## 16.2 Velocity

\[
v_t = \frac{p_t - p_{t-\Delta t}}{\Delta t}
\]

## 16.3 Acceleration

\[
a_t = \frac{v_t - v_{t-\Delta t}}{\Delta t}
\]

Use smoothing to reduce detector jitter.

Recommended:
- moving average,
- Savitzky-Golay,
- exponential smoothing.

Do not use raw 1-frame velocity for event decisions.

---

# 17. Temporal Event Graph

This is one of the main differentiators.

Represent entities:

```text
Person
Product
Pallet
Equipment
Zone
Vehicle
```

Represent relations:

```text
NEAR
TOUCHING
ABOVE
SUPPORTED_BY
INSIDE
MOVING_WITH
HANDLED_BY
COLLIDED_WITH
IN_ZONE
```

Represent events:

```text
PICK_UP
RELEASE
MOVE
DROP
IMPACT
PLACE
DRAG
STACK
ENTER_ZONE
EXIT_ZONE
```

Graph example:

```text
person_3 --HANDLED_BY--> carton_8
carton_8 --ABOVE--> pallet_2
carton_8 --RELEASE--> t=4.2
carton_8 --DOWNWARD_MOTION--> t=4.2–4.7
carton_8 --IMPACT--> floor
```

This graph should be stored only for the short rolling temporal window needed for reasoning.

---

# 18. Behaviour Detector Interface

Create a common interface:

```python
class BehaviourDetector:
    name: str

    def update(self, context) -> list[BehaviourEvidence]:
        raise NotImplementedError
```

Output:

```python
BehaviourEvidence(
    behaviour="drop",
    start_time=4.2,
    end_time=4.8,
    entities=["carton_8"],
    raw_score=0.86,
    evidence={
        "drop_distance_px": 93,
        "peak_speed": 141,
        "impact_deceleration": 188
    }
)
```

---

# 19. Risk Scoring Engine

## 19.1 Separate risk and confidence

Never display one ambiguous number.

Display:

```text
Risk: 82 / 100
Confidence: 0.88
```

### Risk
“How harmful could this situation be?”

### Confidence
“How certain is the system that the behaviour occurred?”

---

# 20. Initial Risk Formula

Prototype formula:

\[
R = 100 \cdot \sigma(
w_b B +
w_s S +
w_i I +
w_d D +
w_f F +
w_l L
)
\]

Where:

- \(B\): behaviour severity.
- \(S\): product sensitivity/fragility.
- \(I\): impact/intensity.
- \(D\): duration.
- \(F\): recurrence/frequency.
- \(L\): location risk.
- \(\sigma\): bounded sigmoid/normalization.

Alternative simple weighted formula:

```text
risk =
0.35 * behaviour_severity +
0.20 * intensity +
0.15 * product_fragility +
0.10 * duration +
0.10 * repeat_frequency +
0.10 * location_risk
```

Map to:

```text
0–24   Low
25–49  Medium
50–74  High
75–100 Critical
```

Tune after validation.

---

# 21. Product Risk Metadata

Create:

```yaml
products:
  default:
    fragility: 0.4
  electronics:
    fragility: 0.9
  mattress:
    fragility: 0.5
  glass:
    fragility: 1.0
```

If product class is unknown:
- use default,
- display “generic product-risk prior”.

Do not claim exact fragility without source metadata.

---

# 22. Incident Engine

An incident is not a single frame.

Incident schema:

```text
incident_id
video_id
camera_id
loading_bay
behaviour
risk_score
risk_level
confidence
start_time
end_time
primary_object_track
actor_track_optional
equipment_track_optional
zone
evidence_json
preview_image
clip_path
explanation
recommendation
status
review_label
supervisor_note
created_at
```

Statuses:

```text
NEW
ACKNOWLEDGED
UNDER_REVIEW
CONFIRMED
FALSE_POSITIVE
RESOLVED
```

---

# 23. Incident Deduplication

Prevent 100 alerts from one drop.

Key:

```text
(behaviour, object_track_id, temporal_window)
```

Rules:
- Merge detections within cooldown.
- Keep highest risk.
- Extend event end time.
- Preserve accumulated evidence.

Example:

```yaml
dedup:
  drop: 4
  drag: 3
  unstable_stack: 10
```

---

# 24. Evidence Clip Generation

For every incident:

```text
pre_event_buffer = 3 seconds
event interval
post_event_buffer = 4 seconds
```

Generated clip:
```text
incident_20260904_001.mp4
```

Overlay:
- bounding boxes,
- track IDs,
- behaviour,
- risk,
- timestamp.

Store a preview thumbnail.

---

# 25. Explanation Engine

Explanation should be evidence-based.

Bad:
> “The employee mishandled the product carelessly.”

Good:
> “A carton moved downward rapidly for 0.6 s, followed by an abrupt stop at floor level. The estimated image-space drop displacement was 91 px. This pattern was classified as a potential drop event.”

Avoid attributing intent.

---

# 26. Recommended Action Engine

Use SOP-backed templates.

Example mapping:

```yaml
drop:
  recommendation: >
    Inspect the product for visible damage and review the unloading
    technique. Use controlled placement and appropriate handling equipment.

drag:
  recommendation: >
    Move the product using a trolley, pallet truck, or approved handling
    device instead of dragging it across the floor.
```

LLM may rephrase but must not invent new policy.

---

# 27. AI Supervisor Assistant

## 27.1 Supported queries

Examples:

- Show high-risk events from today.
- What were the most common risky behaviours?
- Which bay had the highest event count?
- Why was incident HG-102 classified as high risk?
- Show drop incidents.
- How many false positives occurred?
- Summarize the morning shift.
- What corrective actions are recommended?
- Which behaviour increased compared with the previous shift?

---

# 28. Assistant Grounding Architecture

Do not send the entire video to the LLM.

Pipeline:

```text
User question
↓
Intent parser
↓
Approved tool call
↓
Incident DB / analytics query
↓
Structured result
↓
LLM explanation
↓
Citation to incident IDs
```

Tools:

```python
get_incident(id)
list_incidents(filters)
aggregate_behaviours(period)
risk_summary(period)
bay_summary(period)
get_sop(behaviour)
```

Every answer should reference:
- incident IDs,
- time range,
- source counts.

If no data exists:
> “No matching incidents were found.”

Never invent events.

---

# 29. Assistant Guardrails

System rules:

1. Use only tool-returned facts.
2. Never identify a worker.
3. Never infer intent.
4. Never claim confirmed product damage unless a human recorded confirmation.
5. Distinguish observed event from inferred risk.
6. Do not recommend disciplinary action.
7. If data is unavailable, say so.
8. Do not expose sensitive video paths unnecessarily.
9. Mention confidence where appropriate.

---

# 30. Backend API

Minimum endpoints:

```text
POST   /api/videos
GET    /api/videos
GET    /api/videos/{id}
POST   /api/videos/{id}/process

GET    /api/incidents
GET    /api/incidents/{id}
PATCH  /api/incidents/{id}
GET    /api/incidents/{id}/clip

GET    /api/analytics/summary
GET    /api/analytics/behaviours
GET    /api/analytics/risk
GET    /api/analytics/bays

POST   /api/assistant/query

GET    /api/config/behaviours
PATCH  /api/config/behaviours

GET    /api/zones
POST   /api/zones
PATCH  /api/zones/{id}
DELETE /api/zones/{id}
```

---

# 31. Database Tables

Create:

## videos
- id
- filename
- source_type
- duration
- fps
- width
- height
- camera_id
- loading_bay
- status
- created_at

## incidents
- id
- video_id
- behaviour
- risk_score
- risk_level
- confidence
- start_time
- end_time
- zone
- evidence_json
- clip_path
- thumbnail_path
- explanation
- recommendation
- review_status
- created_at

## incident_entities
- incident_id
- track_id
- entity_type
- role

## reviews
- incident_id
- label
- comment
- reviewer_role
- created_at

## zones
- camera_id
- name
- polygon_json
- zone_type

## sop_rules
- behaviour
- rule_text
- recommendation

## metrics_runs
- model_version
- dataset_version
- metrics_json
- timestamp

---

# 32. Dashboard UX

## 32.1 Main dashboard

Display:

```text
Today's Risk Events
Critical
High
Medium
Low

High-risk events per hour
Behaviour distribution
Risk trend
Loading bay comparison
Recent incidents
```

Do not overload with 20 charts.

---

# 33. Video Review Page

Layout:

```text
┌───────────────────────────────┬──────────────────┐
│ Video                         │ Incident details │
│ boxes + overlays              │ risk             │
│                               │ confidence       │
│                               │ evidence         │
│                               │ recommendation   │
├───────────────────────────────┴──────────────────┤
│ Event timeline                                  │
└──────────────────────────────────────────────────┘
```

Controls:
- play/pause,
- incident jump,
- slow playback,
- before/after frames,
- overlay toggle.

---

# 34. Incident Card

Each card:

```text
[HIGH]
Potential Product Drop
20:43:12
Loading Bay A
Risk 82
Confidence 88%

Evidence:
• Downward displacement: 91 px
• Impact-like deceleration detected

[Replay] [Review]
```

---

# 35. Behaviour Analytics

Charts:
- Count by behaviour.
- Risk by behaviour.
- Event frequency over time.
- Bay comparison.
- False-positive rate by behaviour.
- Repeat-event trend.

---

# 36. Human Review Workflow

When supervisor opens event:

```text
System label: Potential drop
Risk: 82
Confidence: 0.88

Review:
[Confirm]
[False positive]
[Needs investigation]

Optional:
Severity override
Note
```

This feedback becomes evaluation data.

---

# 37. Privacy-by-Design

The source challenge explicitly requires responsible use.

Implement:

- No face recognition.
- No worker names.
- Track IDs reset per session.
- Optional face blurring.
- Role-based UI.
- Incident-only video retention option.
- Configurable retention days.
- Audit actions.
- Avoid employee scorecards unless explicitly anonymized/team-level.

---

# 38. Data Retention

Prototype defaults:

```yaml
privacy:
  retain_full_video_days: 7
  retain_incident_clips_days: 30
  blur_faces: true
  store_worker_identity: false
```

Do not delete automatically in demo unless tested.

---

# 39. Explainability

Every incident should include:

```text
Observed:
Product track moved downward 91 px in 0.63 s.

Derived:
Vertical speed exceeded configured threshold.

Reason:
Rapid unsupported downward motion followed by floor-level stop.

Classification:
Potential product drop.

Risk drivers:
Drop magnitude + product class + impact proxy.

Recommended action:
Inspect product and review handling practice.
```

---

# 40. Model Versioning

Store:

```text
detector model
tracker
behaviour config hash
risk config hash
code commit hash
dataset version
```

This allows reproducibility.

---

# 41. Evaluation Framework

The project must report more than accuracy.

## 41.1 Object detection
- Precision.
- Recall.
- mAP50.
- mAP50-95.

## 41.2 Behaviour detection
For each behaviour:
- TP.
- FP.
- FN.
- Precision.
- Recall.
- F1.
- Event IoU / temporal overlap if possible.

## 41.3 Operational metrics
- Detection latency.
- Time to alert.
- Events per shift.
- Repeat events.
- Bay-level event rates.

## 41.4 False alerts
- False positives/hour.
- False alerts/video.
- Supervisor rejection rate.

## 41.5 Assistant
Test factuality:
- 30–50 predetermined queries.
- Exact answerable facts.
- Unsupported-answer rate.
- Incident-ID grounding rate.

---

# 42. Behaviour Metric Definitions

\[
Precision = \frac{TP}{TP+FP}
\]

\[
Recall = \frac{TP}{TP+FN}
\]

\[
F1 = 2\frac{Precision \cdot Recall}{Precision + Recall}
\]

Report per-class and macro average.

Do not show only overall accuracy.

---

# 43. Latency Metrics

Measure:

```text
frame decode
detector
tracker
temporal reasoning
risk scoring
incident generation
API delivery
```

Report:
- mean,
- p50,
- p95.

---

# 44. Event-Level Evaluation

Frame-level accuracy is insufficient.

Ground truth:

```text
drop event: 4.2s–5.0s
```

Prediction:

```text
drop event: 4.35s–5.12s
```

Calculate:
- event matched?
- temporal overlap?
- detection delay?

---

# 45. Threshold Tuning

Never tune thresholds on test set.

Workflow:

```text
Training data
→ model training

Validation data
→ thresholds / risk weights

Test data
→ final evaluation only
```

Document every threshold.

---

# 46. Baselines

For credibility compare:

### Baseline A
Frame-only object detection.

### Baseline B
Object detection + simple single-frame relation rules.

### Proposed
Detection + tracking + temporal reasoning + event graph + risk engine.

Compare:
- behaviour F1,
- false positives,
- event detection latency.

---

# 47. Ablation Study

Useful ablations:

```text
Proposed full system
- no tracking
- no temporal smoothing
- no event graph
- no spatial-zone reasoning
- fixed risk instead of contextual risk
```

Even 2–3 ablations will strengthen the project.

---

# 48. Business Impact Model

Do not fabricate money saved.

Use:

\[
Estimated\ Avoided\ Loss
=
N_p
\times
P_d
\times
C_d
\]

Where:
- \(N_p\) = potentially preventable high-risk events.
- \(P_d\) = assumed/validated probability of damage after such event.
- \(C_d\) = estimated average cost per damaged item.

Clearly label assumptions.

Better for prototype:
- show avoided-risk opportunity,
- not guaranteed savings.

---

# 49. Damage Prevention KPI

Primary KPI:

```text
High-risk handling events identified early enough for intervention
```

Additional:
- repeat behaviour reduction,
- average response time,
- high-risk events per 100 handling actions,
- false-positive rate.

---

# 50. Demo Dataset

Create a deterministic demo pack:

```text
demo/
  01_drop.mp4
  02_drag.mp4
  03_throw.mp4
  04_bad_stack.mp4
  05_unstable_stack.mp4
  06_zone_violation.mp4
  07_pallet_overhang.mp4
  08_step_on_box.mp4
  09_manual_heavy_lift.mp4
  10_unsafe_sequence.mp4
  11_normal_handling.mp4
  12_mixed_shift.mp4
```

The demo should never depend on internet connectivity.

---

# 51. Demo Golden Path

The judge should see:

```text
1. Upload mixed warehouse video.
2. Video begins processing.
3. Tracks appear.
4. A risky event is highlighted.
5. Risk score appears.
6. Incident is created automatically.
7. Replay evidence clip.
8. Explanation shows why.
9. Recommendation appears.
10. Dashboard count updates.
11. Ask assistant:
   "Why was incident HG-001 high risk?"
12. Assistant retrieves the incident and explains it.
13. Supervisor confirms / rejects.
14. Analytics refresh.
```

---

# 52. Real-Time Alerting

For prototype:

```text
Critical → red banner + sound optional
High → prominent notification
Medium → dashboard queue
Low → analytics only
```

Avoid constant noisy alerts.

Implement throttling.

---

# 53. Notification Payload

```json
{
  "incident_id": "HG-001",
  "behaviour": "drop",
  "risk": 82,
  "confidence": 0.88,
  "time": "20:43:12",
  "bay": "A",
  "message": "Potential high-risk product drop detected."
}
```

---

# 54. Configuration UI

Admin can change:
- enabled behaviours,
- risk thresholds,
- zone polygons,
- retention,
- alert threshold.

Do not expose unsafe raw model internals.

---

# 55. Testing Plan

## Unit tests
Test:
- geometry functions.
- velocity.
- acceleration.
- zone membership.
- risk score.
- deduplication.
- configuration parsing.

## Integration tests
Test:
```text
sample video
→ detections
→ incident
→ DB
→ API
→ dashboard
```

## Regression tests
Use fixed demo clips and expected incidents.

Example:
```text
01_drop.mp4 must produce >=1 DROP incident.
normal_handling.mp4 must not produce Critical incident.
```

---

# 56. Error Handling

Handle:
- corrupt video.
- unsupported codec.
- missing FPS.
- model load failure.
- no detections.
- tracker failure.
- DB failure.
- LLM unavailable.
- malformed config.
- missing incident clip.

Frontend must show clear errors.

---

# 57. Offline / Graceful Degradation

If LLM fails:
- core CV pipeline must continue.
- incident explanations fall back to templates.

If internet fails:
- prerecorded demo still works.

If GPU unavailable:
- use lower input size / sampling FPS.

---

# 58. Performance Optimization

Use:
- frame skipping.
- resized inference.
- batch where possible.
- model warmup.
- mixed precision if supported.
- no unnecessary image copies.
- bounded track history.
- incident-only clip storage.

---

# 59. Logging

Structured logs:

```text
timestamp
level
video_id
module
event
latency_ms
error
```

Never log raw confidential data unnecessarily.

---

# 60. Observability

Dashboard/dev panel:
- current FPS.
- processing latency.
- model loaded.
- queued videos.
- incident count.
- error count.

---

# 61. Security

Minimum:
- Validate uploads.
- Restrict file types.
- Limit maximum upload size.
- Sanitize filenames.
- No arbitrary path reads.
- CORS restriction.
- Secrets in `.env`.
- Do not commit keys.
- Validate assistant tool calls.
- Rate limit assistant endpoint if exposed publicly.

---

# 62. Responsible AI Statement

Document:

- System analyzes behaviour, not identity.
- Risk events are decision support.
- Alerts are subject to human review.
- Detection does not establish misconduct.
- Detection does not establish confirmed product damage.
- No automatic disciplinary action.
- Confidence and evidence are shown.
- Data retention should be limited.

---

# 63. User Validation

Need at least a small validation activity.

Potential reviewers:
- logistics student,
- faculty member,
- lab supervisor,
- operations professional,
- warehouse/logistics contact.

Ask each user:

1. Could you understand the incident?
2. Was evidence sufficient?
3. Was risk level intuitive?
4. Was the corrective action useful?
5. Was dashboard easy to navigate?
6. Which alerts seemed unnecessary?
7. What information was missing?
8. Would this help prevent repeated handling errors?

Record changes made based on feedback.

---

# 64. User Validation Table

Create:

| Feedback | Before | Change | After |
|---|---|---|---|
| Risk score unclear | One score | Added risk + confidence | Better interpretability |
| Alert too vague | "Unsafe event" | Added evidence factors | Clear reason |
| Video too long | Full video | Added 7-sec replay clip | Faster review |

---

# 65. README Requirements

README must contain:

1. Problem.
2. Solution.
3. Architecture.
4. Demo GIF/screenshot.
5. Features.
6. Behaviours.
7. Technology stack.
8. Installation.
9. Run commands.
10. Dataset.
11. Model information.
12. Evaluation.
13. Responsible AI.
14. Limitations.
15. Roadmap.
16. Team.
17. License.
18. Demo video link.

---

# 66. Installation

Target:

```bash
git clone <repo>
cd handleguard-ai

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

uvicorn apps.api.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

---

# 67. Docker

Create:

```text
backend Dockerfile
frontend Dockerfile
docker-compose.yml
```

Services:

```text
api
web
postgres optional
```

For prototype, do not add Kafka/Redis unless actually necessary.

---

# 68. Demo Seed

Create:

```bash
python scripts/seed_demo.py
```

It should:
- add sample videos,
- create zones,
- create SOPs,
- optionally preload sample incidents if model demo fails.

Important: clearly mark seeded sample incidents versus AI-generated incidents.

---

# 69. Submission Evidence Folder

Store:

```text
artifacts/
  evaluation/
    metrics.json
    per_class.csv
    latency.csv
    confusion_matrix.png
  screenshots/
    dashboard.png
    incident.png
    replay.png
    assistant.png
  figures/
    architecture.png
    event_graph.png
    pipeline.png
  reports/
    user_feedback.pdf
    evaluation_report.md
```

---

# 70. Required Screenshots

Capture:

1. Upload page.
2. AI-overlay video.
3. Drop event.
4. Drag event.
5. Stack event.
6. Risk card.
7. Incident replay.
8. Dashboard.
9. Analytics.
10. Assistant query.
11. Human review.
12. Settings/privacy.

---

# 71. Presentation Structure

The challenge expects a short deck. Keep six slides.

## Slide 1 — Solution & Team
- HandleGuard AI.
- One-line value proposition.
- Team.

## Slide 2 — Problem + User Journey
```text
Video
→ Understand
→ Detect
→ Assess
→ Alert
→ Intervene
→ Learn
```

## Slide 3 — Technical Architecture
Include:
- detector,
- tracker,
- temporal graph,
- risk engine,
- database,
- assistant,
- dashboard.

## Slide 4 — Prototype
Use real screenshots.

## Slide 5 — Evaluation + Impact
Show:
- behaviour F1,
- latency,
- false positive rate,
- user feedback,
- risk-prevention metrics.

## Slide 6 — Innovation + Responsible AI + Roadmap
Highlight:
- temporal event graph,
- evidence-grounded assistant,
- prevention focus,
- privacy-by-design.

---

# 72. Five-Minute Demo Script

### 0:00–0:30
Problem:
Traditional CCTV records incidents; HandleGuard tries to identify risky handling early.

### 0:30–1:00
Show architecture.

### 1:00–2:30
Run video:
- detection,
- tracking,
- temporal event,
- risk alert.

### 2:30–3:15
Replay incident and explanation.

### 3:15–4:00
Dashboard and analytics.

### 4:00–4:30
Ask assistant a grounded query.

### 4:30–5:00
Results + prevention + responsible AI.

---

# 73. Judging-Criteria Optimization

## Innovation & Creativity
Evidence:
- temporal event graph,
- explainable risk,
- assistant grounding,
- prevention-first workflow.

## Technical Execution
Evidence:
- functioning pipeline,
- tracking,
- temporal rules,
- database,
- API,
- dashboard,
- tests.

## AI + Video Intelligence
Evidence:
- temporal behavior understanding,
- at least 10 behaviours,
- event-level metrics.

## UX & User Feedback
Evidence:
- replay-first workflow,
- user study,
- iteration.

## Damage Prevention & Business Impact
Evidence:
- preventive alerts,
- response-time KPI,
- repeat-behaviour trends,
- transparent impact model.

## Presentation
Evidence:
- concise deck,
- reproducible demo,
- real screenshots,
- measurable results.

---

# 74. Development Order

Do not build randomly.

## Phase 1 — Foundation
- repo structure,
- env,
- video upload,
- detector,
- tracker,
- overlay.

## Phase 2 — Temporal engine
- track history,
- velocity,
- geometry,
- zones,
- event graph.

## Phase 3 — Behaviours
Implement easiest first:

1. zone violation
2. dragging
3. drop
4. pallet overhang
5. unstable stack
6. improper stacking
7. rough handling
8. throwing
9. stepping on package
10. unsafe manual handling
11. unsafe sequence
12. unsafe surface

## Phase 4 — Risk + incidents
- risk,
- dedup,
- clips,
- explanation.

## Phase 5 — Dashboard
- list,
- detail,
- replay,
- analytics.

## Phase 6 — Assistant
- DB tools,
- safe prompts,
- factuality tests.

## Phase 7 — Evaluation
- annotations,
- metrics,
- latency,
- error analysis.

## Phase 8 — Submission
- screenshots,
- deck,
- demo,
- README.

---

# 75. Six-Day Sprint Plan

Assuming work starts immediately and submission is 10 September 2026.

## Day 1 — Core pipeline
- final repo setup.
- video upload.
- detector.
- tracker.
- basic overlay.
- DB.
- one test video.

**Exit condition:** Stable tracked objects visible.

## Day 2 — Temporal reasoning
- histories.
- geometry.
- zones.
- velocity/acceleration.
- event graph.
- implement 4 simple behaviours.

**Exit condition:** Four behaviours generate incidents.

## Day 3 — Reach 10 behaviours
- implement remaining behaviour logic.
- risk engine.
- deduplication.
- incident clips.

**Exit condition:** Ten behaviours can be demonstrated.

## Day 4 — Product layer
- dashboard.
- incident review.
- analytics.
- AI assistant.
- privacy.

**Exit condition:** End-to-end supervisor workflow works.

## Day 5 — Evaluation
- test dataset.
- metrics.
- false-positive analysis.
- latency.
- threshold tuning.
- user feedback.

**Exit condition:** Real metrics available.

## Day 6 — Submission hardening
- fix regression failures.
- screenshots.
- final deck.
- demo recording.
- README.
- backup demo.
- final checklist.

---

# 76. Priority Classification

## P0 — Must exist
- video ingestion.
- detection.
- tracking.
- 10 behaviours.
- risk scoring.
- incidents.
- evidence clips.
- dashboard.
- AI explanation.
- demo.
- metrics.

## P1 — Strongly recommended
- event graph.
- user feedback.
- assistant grounding.
- privacy controls.
- review workflow.
- ablation.

## P2 — Stretch
- RTSP.
- multi-camera.
- voice alerts.
- edge export.
- WMS integration.
- 3D view.

---

# 77. Behaviour Implementation Tickets

## Ticket B01
**Name:** Drop detector  
**Files:** `behaviours/drop.py`  
**Inputs:** product history, floor relation  
**Outputs:** BehaviourEvidence  
**Tests:** gentle placement false, drop true  
**Acceptance:** detects staged drop with no duplicate alerts.

## Ticket B02
**Name:** Drag detector  
**Files:** `behaviours/drag.py`  
**Acceptance:** sustained floor movement triggers; lifted movement does not.

## Ticket B03
**Name:** Throw detector  
**Acceptance:** unsupported fast horizontal motion triggers.

## Ticket B04
**Name:** Rough handling  
**Acceptance:** abrupt impact pattern triggers but smooth placement does not.

## Ticket B05
**Name:** Improper stack  
**Acceptance:** large-on-small violation detected.

## Ticket B06
**Name:** Unstable stack  
**Acceptance:** low support ratio / overhang triggers.

## Ticket B07
**Name:** Zone violation  
**Acceptance:** persistent invalid placement triggers after configurable delay.

## Ticket B08
**Name:** Pallet overhang  
**Acceptance:** product unsupported beyond threshold triggers.

## Ticket B09
**Name:** Stepping on product  
**Acceptance:** foot-product spatial contact sustained for threshold triggers.

## Ticket B10
**Name:** Manual heavy handling  
**Acceptance:** large product + person + no approved equipment produces risk event.

## Ticket B11
**Name:** Unsafe sequence  
**Acceptance:** finite-state SOP violation detected.

## Ticket B12
**Name:** Unsafe surface  
**Acceptance:** product movement through configured unsafe zone triggers.

---

# 78. Frontend Tickets

## F01 Dashboard shell
Acceptance:
- responsive.
- no broken states.

## F02 Video upload
Acceptance:
- upload progress.
- invalid file validation.

## F03 Processing status
Acceptance:
- queued / processing / complete / error.

## F04 Incident list
Acceptance:
- filters.
- sorting.
- pagination or bounded list.

## F05 Incident detail
Acceptance:
- replay.
- risk.
- confidence.
- evidence.
- recommendation.

## F06 Review form
Acceptance:
- confirm.
- false positive.
- note.

## F07 Analytics
Acceptance:
- behaviour.
- risk.
- trends.

## F08 Assistant
Acceptance:
- grounded results.
- source incident IDs.

## F09 Privacy/settings
Acceptance:
- zone configuration.
- behaviour toggles.
- retention controls.

---

# 79. Backend Tickets

## A01 Video API
## A02 Processing job
## A03 Incident API
## A04 Analytics aggregation
## A05 Review API
## A06 Zone API
## A07 Assistant tools
## A08 Report export
## A09 Health endpoint

Health endpoint:

```json
{
  "api": "ok",
  "db": "ok",
  "detector": "loaded",
  "version": "0.1.0"
}
```

---

# 80. Test Cases

## Drop
- true drop.
- gentle placement.
- detector jitter.
- occluded drop.
- product falls behind pallet.

## Drag
- actual drag.
- carry at low height.
- trolley movement.
- stationary package.

## Stack
- correct.
- top-heavy.
- slight overhang.
- major overhang.

## Zone
- transient crossing.
- persistent placement.
- center outside but footprint inside.

## Assistant
- valid query.
- query with no matching incidents.
- prompt-injection attempt.
- request for employee identity.
- request to claim confirmed damage.

---

# 81. False-Positive Analysis

For each false positive record:

```text
Incident
Behaviour
Why system triggered
Why human rejected
Signal responsible
Fix
```

Categories:
- tracking jitter.
- occlusion.
- perspective.
- threshold.
- class confusion.
- zone geometry.
- duplicate event.
- intentional safe handling.

---

# 82. Model/Error Cards

For every behaviour:

```text
What it detects
What it does not detect
Known failure conditions
Required camera view
Minimum object visibility
Calibration status
```

This improves credibility.

---

# 83. Camera Guidance

Document:
- fixed camera preferred.
- avoid extreme fisheye.
- loading area visible.
- floor/pallet boundaries visible.
- 720p minimum preferred.
- stable frame.
- adequate lighting.

---

# 84. Calibration

For approximate geometric quantities:
- calibrate pixels-to-distance using known reference.
- otherwise report image-space proxy.

Never say:
> “1.00 metre drop”

unless calibration supports it.

Say:
> “estimated ~1 m under calibrated scene geometry”

or:
> “91 px vertical drop proxy.”

---

# 85. Risk Calibration

After validation:
- plot confidence reliability.
- compare risk level with human severity labels.
- adjust thresholds.

At minimum report:
- confusion matrix between predicted risk category and reviewer category.

---

# 86. Assistant Evaluation Set

Create 40 questions:

```text
10 factual incident queries
10 aggregation queries
10 explanation queries
5 no-answer queries
5 unsafe/inappropriate queries
```

Pass conditions:
- no invented incidents.
- correct counts.
- incident IDs included.
- refuses unsupported identity/punitive inference.

---

# 87. Documentation Files

Create:

```text
docs/architecture.md
docs/behaviour_taxonomy.md
docs/dataset.md
docs/annotation.md
docs/risk_model.md
docs/responsible_ai.md
docs/evaluation.md
docs/demo_script.md
docs/user_validation.md
docs/limitations.md
```

---

# 88. Architecture Diagram Requirements

The diagram must visibly contain:

```text
Video
Detection
Tracking
Temporal features
Event graph
Behaviour intelligence
Risk engine
Incident manager
Database
Dashboard
AI assistant
Human review
```

Arrows should show data flow.

---

# 89. Event Graph Diagram

Show one event:

```text
Person
  |
HANDLES
  ↓
Carton
  |
RELEASED
  ↓
Downward movement
  |
IMPACT
  ↓
Potential Drop
  |
Risk Engine
  ↓
High Risk
```

---

# 90. Demo Reliability Checklist

Before recording:

- [ ] Fresh restart works.
- [ ] Models load.
- [ ] Sample videos present.
- [ ] No internet dependency.
- [ ] Database seeded.
- [ ] Video path valid.
- [ ] At least 3 flagship incidents detect reliably.
- [ ] Assistant works.
- [ ] Dashboard counts update.
- [ ] No secrets visible.
- [ ] Browser console clean.
- [ ] No stack traces.
- [ ] Audio disabled unless intentional.

---

# 91. Flagship Demo Behaviours

Make these extremely reliable:

1. Drop.
2. Drag.
3. Unstable/improper stack.
4. Zone violation.
5. Pallet overhang.

Other five can be shown via separate clips.

---

# 92. Demo Failure Backup

Have:
- prerecorded demo video.
- screenshots.
- saved incident clips.
- evaluation CSV.
- offline seed data.

If live inference fails, never be left without proof.

---

# 93. Project Claims You MAY Make

Good:
- “The prototype detects predefined risk-indicating handling behaviours.”
- “The system uses temporal track history rather than only isolated frames.”
- “Risk scores are explainable using configured factors.”
- “The assistant is grounded in stored incidents.”
- “The system is designed for preventive intervention.”

---

# 94. Claims You MUST NOT Make Without Evidence

Do not claim:
- 99% accuracy.
- zero false positives.
- guaranteed damage prevention.
- worker intent.
- exact force.
- exact damage probability.
- exact money saved.
- production readiness.
- universal warehouse generalization.

---

# 95. Submission Metrics Table Template

| Metric | Result |
|---|---:|
| Behaviours supported | TBD |
| Behaviour macro precision | TBD |
| Behaviour macro recall | TBD |
| Behaviour macro F1 | TBD |
| False alerts/hour | TBD |
| Median detection latency | TBD |
| p95 detection latency | TBD |
| Assistant factual accuracy | TBD |
| User feedback score | TBD |
| Critical demo failures | 0 target |

Replace TBD only with executed results.

---

# 96. Per-Behaviour Results Template

| Behaviour | Precision | Recall | F1 | Test Events |
|---|---:|---:|---:|---:|
| Drop | TBD | TBD | TBD | TBD |
| Drag | TBD | TBD | TBD | TBD |
| Throw | TBD | TBD | TBD | TBD |
| Rough Handling | TBD | TBD | TBD | TBD |
| Improper Stack | TBD | TBD | TBD | TBD |
| Unstable Stack | TBD | TBD | TBD | TBD |
| Zone Violation | TBD | TBD | TBD | TBD |
| Pallet Overhang | TBD | TBD | TBD | TBD |
| Stepping | TBD | TBD | TBD | TBD |
| Manual Heavy Handling | TBD | TBD | TBD | TBD |

---

# 97. Acceptance Criteria for Final Build

The build passes only if:

- [ ] Clean installation succeeds.
- [ ] Backend starts with one command.
- [ ] Frontend starts with one command.
- [ ] Upload accepts valid sample video.
- [ ] Processing does not crash.
- [ ] Detector outputs objects.
- [ ] Tracker maintains IDs.
- [ ] At least 10 behaviours implemented.
- [ ] At least 10 behaviours have demo evidence.
- [ ] Incident risk stored.
- [ ] Risk and confidence separated.
- [ ] Incident clips generated.
- [ ] Dashboard renders.
- [ ] Review flow works.
- [ ] Assistant queries DB.
- [ ] Assistant does not invent incidents.
- [ ] Metrics are generated.
- [ ] README is accurate.
- [ ] No fake results.
- [ ] Privacy statement present.
- [ ] Presentation screenshots current.
- [ ] Demo video recorded.

---

# 98. Red-Team Review Before Submission

Ask:

### Technical
- Can the system work without the LLM?
- Are temporal claims truly temporal?
- Are events deduplicated?
- Are test clips independent?

### Scientific
- Are results reproducible?
- Were thresholds tuned on validation data?
- Are unsupported physical quantities avoided?

### Product
- Does each alert enable action?
- Is evidence replay fast?
- Can supervisor correct mistakes?

### Responsible AI
- Are employees identified?
- Is intent inferred?
- Can false positives harm workers?
- Is human review explicit?

### Presentation
- Does every claim have proof?
- Are optional future features clearly separated from current build?

---

# 99. Final Repository Cleanup

Delete:
- temporary videos.
- huge model caches.
- `.env`.
- API keys.
- dead code.
- duplicate scripts.
- notebook checkpoints.
- debug dumps.

Add:
- `.gitignore`.
- example config.
- small demo assets only.
- reproducible setup.

---

# 100. Git Workflow

Branches:
```text
main
dev
feature/video
feature/tracking
feature/behaviours
feature/dashboard
feature/assistant
```

Commit messages:
```text
feat: add temporal drop detector
fix: deduplicate repeated drag events
test: add geometry regression cases
docs: document risk scoring
```

Before submission:
- merge to main.
- tag:
```text
v1.0-submission
```

---

# 101. Issue Tracker

Every task should have:
- owner.
- priority.
- deadline.
- acceptance criteria.
- dependencies.
- status.

Statuses:
```text
TODO
IN PROGRESS
BLOCKED
REVIEW
DONE
```

---

# 102. Team Split for 3 People

## Member A — CV / ML
- detector.
- tracker.
- temporal features.
- behaviours.
- metrics.

## Member B — Backend / AI
- API.
- DB.
- risk engine.
- incident manager.
- assistant.

## Member C — Frontend / Product
- dashboard.
- video replay.
- analytics.
- testing.
- presentation/demo.

Shared:
- data collection.
- user feedback.
- final integration.

---

# 103. Team Split for 4–5 People

## CV engineer
Perception/tracking.

## Behaviour engineer
Temporal/event logic.

## Backend/AI engineer
API/assistant/database.

## Frontend engineer
Dashboard.

## Product/evaluation lead
Dataset, metrics, user validation, presentation.

---

# 104. Daily Integration Rule

Every day:
1. Pull latest main.
2. Run tests.
3. Merge one stable vertical slice.
4. Update demo branch.
5. Record blockers.

Avoid waiting until final day to integrate.

---

# 105. Minimum Vertical Slice

First end-to-end feature:

```text
Upload video
→ detect carton
→ track carton
→ detect drop
→ score risk
→ create incident
→ save clip
→ show incident
```

Finish this before adding many behaviours.

---

# 106. Stretch Features Only After Core Passes

Possible stretch:

- multilingual voice alert.
- PPE detection.
- forklift/pedestrian proximity.
- loading-plan verification.
- multi-camera tracking.
- edge deployment.
- WMS integration.
- digital twin.
- predictive shift-level risk.

Do not compromise core quality for these.

---

# 107. Future Research Extensions

After submission:

1. Learned temporal action recognition.
2. Vision-language incident reasoning.
3. Self-supervised anomaly detection.
4. Camera calibration.
5. 3D pose / depth.
6. Multi-camera entity fusion.
7. Counterfactual risk explanation.
8. Risk forecasting.
9. Federated warehouse learning.
10. Domain adaptation across sites.

---

# 108. Possible Research Questions

If converting to paper:

- Does temporal event-graph reasoning reduce false positives compared with frame-only rules?
- Does evidence-backed risk explanation improve supervisor trust?
- Can hybrid rule + learned video intelligence generalize with limited warehouse data?
- How does camera viewpoint affect behaviour detection?
- Does human-in-the-loop calibration reduce false-alert burden?

These are future research directions, not current results.

---

# 109. Final Submission Package

Submit/store:

```text
01_source_code/
02_demo_video/
03_presentation/
04_architecture/
05_evaluation/
06_user_feedback/
07_readme/
08_sample_data/
09_model_info/
10_responsible_ai/
```

---

# 110. Final 24-Hour Checklist

## Functionality
- [ ] App loads.
- [ ] Video works.
- [ ] 10 behaviours work.
- [ ] Incident replay works.
- [ ] Assistant works.
- [ ] Dashboard works.

## Evidence
- [ ] Metrics exported.
- [ ] Screenshots captured.
- [ ] User feedback documented.
- [ ] Demo recorded.

## Quality
- [ ] No fake results.
- [ ] No broken links.
- [ ] No secrets.
- [ ] No missing dependencies.
- [ ] README verified from clean clone.

## Submission
- [ ] Deck is 5–6 slides.
- [ ] Demo representative scenarios included.
- [ ] Architecture visible.
- [ ] Business impact explained.
- [ ] Privacy addressed.
- [ ] Submission form completed before deadline.

---

# 111. Master “Done” Checklist

## Product
- [ ] Clear prevention value proposition
- [ ] User journey
- [ ] Behaviour taxonomy

## Data
- [ ] Video sources documented
- [ ] Annotation
- [ ] leakage-safe split
- [ ] negative examples

## AI/CV
- [ ] detector
- [ ] tracker
- [ ] temporal features
- [ ] event graph
- [ ] 10+ behaviours
- [ ] risk engine

## Incident Intelligence
- [ ] deduplication
- [ ] evidence clips
- [ ] explanation
- [ ] recommendations
- [ ] review status

## Software
- [ ] FastAPI
- [ ] database
- [ ] frontend
- [ ] tests
- [ ] logging
- [ ] Docker

## Assistant
- [ ] tool-grounded
- [ ] no hallucinated events
- [ ] safe fallback
- [ ] factuality test

## Evaluation
- [ ] detection metrics
- [ ] behaviour metrics
- [ ] latency
- [ ] false positives
- [ ] error analysis
- [ ] assistant evaluation

## Responsible AI
- [ ] no face recognition
- [ ] no identity ranking
- [ ] human review
- [ ] retention
- [ ] explainability
- [ ] privacy

## Submission
- [ ] 5–6 slide deck
- [ ] demo
- [ ] screenshots
- [ ] user validation
- [ ] GitHub README
- [ ] final tag

---

# 112. Final Project Principle

The strongest implementation is not the one with the largest model or the most optional features.

It is the one that can consistently demonstrate:

```text
Observed warehouse behaviour
        ↓
Temporal evidence
        ↓
Explainable risk
        ↓
Actionable intervention
        ↓
Measurable prevention
```

Everything in the repository should support that chain.

If a feature does not strengthen **detection, temporal understanding, risk interpretation, intervention, prevention, usability, evaluation, or responsible deployment**, it should not take priority before the submission.
