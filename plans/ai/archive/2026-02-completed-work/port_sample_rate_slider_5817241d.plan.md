---
name: Port Sample Rate Slider
overview: Port the sample_rate slider from the alpha-improvements Streamlit visualizer into the main branch's React UI, adding it as a feature in the Market Tick Data viewer page.
todos:
  - id: add-slider-ui
    content: Add sample_rate slider (1-1000, default 100) to MarketTickData.tsx React component
    status: pending
  - id: update-api-route
    content: Add sample_rate query parameter to visualizer-api tick data endpoint
    status: pending
  - id: implement-downsampling
    content: Implement tick data downsampling logic in the API service layer
    status: pending
isProject: false
---

# Port Sample Rate Slider to React UI

## Current State Analysis

**Branch Relationship**: `alpha-improvements` is a direct ancestor of `main`. All commits from alpha-improvements are already in main, which has 28 additional commits with:

- TWAP/VWAP algorithm improvements (already merged)
- React/TypeScript UI replacing Streamlit
- Enhanced config infrastructure

**What Needs Porting**: The sample_rate slider from the Streamlit visualizer for tick data loading.

## Source: Alpha-Improvements Streamlit Slider

```100:105:visualizer/app.py (alpha-improvements)
sample_rate = st.slider("Sample rate (1 = all ticks, higher = faster load)", 1, 1000, 100)
```

Used in `load_tick_data()` function to downsample tick data for faster loading.

## Target: React UI Market Tick Data Page

File: [visualizer-ui/src/pages/MarketTickData.tsx](visualizer-ui/src/pages/MarketTickData.tsx)

### Implementation Steps

1. **Add sample_rate state and slider UI** to MarketTickData.tsx
  - Add useState for sampleRate (default: 100)
  - Add a range input slider with label
  - Pass sampleRate to the API call
2. **Update visualizer-api** to accept sample_rate parameter
  - File: [visualizer-api/app/api/routes/analysis.py](visualizer-api/app/api/routes/analysis.py) or create new tick data route
  - Add `sample_rate: int = Query(100, ge=1, le=1000)` parameter
  - Pass to data loading function
3. **Update data loading service** to use sample_rate
  - Implement downsampling logic similar to alpha-improvements:

## Alternative: Keep Both UIs

If you want to keep the Streamlit visualizer alongside React:

- Copy `visualizer/` directory from alpha-improvements to main
- Add it as an alternative tool (Streamlit runs on different port)
- No merge conflicts since main doesn't have this directory

## No Algo Cherry-Picking Needed

The TWAP/VWAP improvements you mentioned are already in main:

- Main has enhanced parameter support (`num_intervals` + `target_intervals`)
- Main has better logging and validation
- Main has additional algorithms (`selector.py`, `sor_twap.py`, etc.)

If you find specific bug fixes in alpha-improvements that are missing from main, please specify the exact code sections.