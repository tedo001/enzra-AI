# User Manual

## The dashboard at a glance

Open **http://localhost:3000**.

```
┌──────────────────────────────────────────────────────────────┐
│ 🚆 RailVision AI                                  ● Streaming │
├──────────────────────────────────────────────────────────────┤
│ [ ALERT BANNER ]  level + recommendation (colour-coded)       │
├───────────┬───────────┬───────────┬───────────────────────────┤
│    FPS    │ On-Track  │ Top Risk  │        Closest            │
├───────────┴───────────┴───────────┴───────────────────────────┤
│                              │  ◔ Risk Gauge (0–100)          │
│      LIVE FEED               │                                │
│  (boxes + corridor + IDs)    │  Obstacles On Track            │
│                              │  • Human #3  42m  R88          │
├──────────────────────────────┴───────────────────────────────┤
│  Obstacle Frequency (chart)          │   System Status        │
└──────────────────────────────────────────────────────────────┘
```

## Reading the feed

- **Green trapezoid** — the railway corridor. Only obstacles whose *foot point*
  falls inside it are treated as on-track hazards.
- **Box colour** — the obstacle's alert level (grey = off-track, ignored).
- **Label** — `Class  #TrackID  Distance  RiskScore`.

## Alert levels

| Level | Colour | Meaning | Recommended action |
|---|---|---|---|
| Safe | green | track clear | normal operation |
| Low | teal | obstacle near corridor | stay alert, monitor |
| Medium | amber | obstacle on track | reduce speed, sound horn |
| High | orange | hazard on track | service brake, prepare to stop |
| Critical | red (pulsing) | collision imminent | **emergency brake now** |

## Voice alerts

When enabled (`RV_ENABLE_VOICE_ALERTS=true`), the dashboard speaks escalating
warnings via the browser's speech synthesis, throttled by a cooldown so it
never storms the operator. Click anywhere once to satisfy browser autoplay
policies.

## Metrics explained

- **FPS** — processed frames per second (target 30+ on GPU).
- **On-Track Obstacles** — count inside the corridor.
- **Top Risk** — highest risk score (0–100) this frame.
- **Closest** — nearest on-track obstacle distance (ground-plane estimate).
- **TTC** — time-to-collision in seconds (per obstacle in the list).

## Incidents

When the overall alert reaches **High** or above, RailVision AI automatically
saves an evidence bundle: an annotated snapshot, a short video clip, a log line
and a JSON metadata sidecar, and records it in the database. Review them under
**Analytics → incident history** (`GET /api/analytics/incidents`).

## Analytics

- **Daily report** — totals, obstacle frequency, incidents by level.
- **Obstacle frequency chart** — which hazards appear most often today.
- **Incident history** — recent recorded events with class, distance and risk.

## Calibration tips

Distance accuracy depends on camera calibration in `.env`:

- `RV_CAMERA_HEIGHT_M` — camera height above the rail.
- `RV_CAMERA_FOCAL_PX` — focal length in pixels (from a calibration pass).
- `RV_TRACK_GAUGE_M` — rail gauge for scale reference.

Set `RV_TRAIN_SPEED_KMH` (or feed live GPS speed) so time-to-collision and
risk scores reflect real closing speed.
