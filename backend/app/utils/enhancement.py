"""Image enhancement for adverse conditions (bonus features).

Classical, real-time CV enhancers that improve detection robustness without an
extra network in the hot path:

* :func:`enhance_night` — CLAHE on the luminance channel for low-light.
* :func:`enhance_fog`   — dark-channel–inspired contrast stretch to cut haze.
* :func:`enhance_rain`  — median/bilateral blend to suppress rain streaks.
* :func:`classify_weather` — cheap heuristic (brightness + saturation +
  contrast) that labels a frame day/night/fog/rain to auto-select an enhancer.

All functions accept and return BGR ``uint8`` arrays and are no-ops if OpenCV
is unavailable, keeping imports safe in minimal environments.
"""

from __future__ import annotations

from enum import Enum

import numpy as np

try:  # pragma: no cover - environment dependent
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


class Weather(str, Enum):
    DAY = "day"
    NIGHT = "night"
    FOG = "fog"
    RAIN = "rain"


def classify_weather(frame: np.ndarray) -> Weather:
    """Fast heuristic weather/condition classifier."""
    gray = frame.mean(axis=2) if frame.ndim == 3 else frame
    brightness = float(gray.mean())
    contrast = float(gray.std())

    if brightness < 60:
        return Weather.NIGHT
    if contrast < 35 and brightness > 120:
        return Weather.FOG
    if cv2 is not None:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sat = float(hsv[..., 1].mean())
        if sat < 40 and contrast < 55:
            return Weather.RAIN
    return Weather.DAY


def enhance_night(frame: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l_chan, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_chan = clahe.apply(l_chan)
    return cv2.cvtColor(cv2.merge((l_chan, a, b)), cv2.COLOR_LAB2BGR)


def enhance_fog(frame: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return frame
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y = cv2.normalize(y, None, 0, 255, cv2.NORM_MINMAX)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    y = clahe.apply(y)
    return cv2.cvtColor(cv2.merge((y, cr, cb)), cv2.COLOR_YCrCb2BGR)


def enhance_rain(frame: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return frame
    smoothed = cv2.bilateralFilter(frame, 7, 60, 60)
    return cv2.addWeighted(frame, 0.4, smoothed, 0.6, 0)


ENHANCERS = {
    Weather.NIGHT: enhance_night,
    Weather.FOG: enhance_fog,
    Weather.RAIN: enhance_rain,
}


def auto_enhance(frame: np.ndarray) -> tuple[np.ndarray, Weather]:
    """Classify then apply the matching enhancer (identity for DAY)."""
    weather = classify_weather(frame)
    enhancer = ENHANCERS.get(weather)
    return (enhancer(frame) if enhancer else frame), weather
