# BB_Liquidity_Bot (v7.41) - Strategy & Architecture Document

## 1. Overview and Core Architecture
This Expert Advisor (EA), currently named `bands_swweps.mq5` (v7.41), is a sophisticated multi-timeframe (MTF) trading bot built for MetaTrader 5 (MQL5). It combines traditional technical indicators (Bollinger Bands, ATR, RSI, ADX) with Smart Money Concepts (SMC) such as internal liquidity sweeps and structural analysis.

The architecture is built around a standard event-driven loop (`OnTick`), heavily modularized into distinct phases:
1.  **Data Acquisition:** Indicator buffer updates (M1, M5, H1 timeframes).
2.  **Market Structure Analysis:** Scanning for internal liquidity, fractals, and structural clearance.
3.  **State Evaluation:** Assessing trend, zones, news, and volatility to populate a comprehensive state matrix.
4.  **Execution & Management:** Condition-based entries (with deceleration options) and advanced dynamic trade management.
5.  **Visualization:** Rendering a real-time dashboard and chart objects (liquidity lines, RSI zones, fib levels).

## 2. Trading Strategy (Entry Logic)
The entry mechanism requires a confluence of macro context, mid-level zoning, and micro-level execution.

### A. Macro Context (H1)
*   **Trend Filter:** Determines the bias using either Bollinger Band (BB) Slope or ADX.
*   **RSI-Adaptive Zones:** The permitted entry zone near the H1 BB extremes dynamically expands or contracts based on H1 RSI momentum. Strong momentum against the desired entry tightens the zone; weak momentum widens it (up to a hard cap of 25% of the band).
*   **Counter-Trend (CT) Bypass:** Generally blocks trading against the H1 trend, *unless* a sudden, large price spike occurs (measured in ATR multipliers), indicating exhaustion.

### B. Mid-Level Context (M5 & Premium/Discount)
*   **M5 Extreme Zone:** Price must reside within the top/bottom percentage (default 25%) of the M5 Bollinger Bands.
*   **Fibonacci 50% Rule:** The bot calculates the recent M1 range (based on a lookback) and only executes Buy orders in the "Discount" zone (below the 50% mark) and Sell orders in the "Premium" zone.

### C. Micro Execution & Confluence (M1)
*   **Internal Liquidity Sweeps:** The EA maps major swing highs/lows and Equal Highs/Lows (EQH/EQL) using fractals. A valid entry *requires* price to sweep (pierce) these liquidity pools. It also includes "Deep Sweep" requirements for major levels.
*   **Structural Clearance:** Prevents entries if immediate micro-structure resistance/support is too close (measured via recent opposing fractals).
*   **Volatility Squeeze Filter:** Adjusts the M1 extreme entry thresholds if a volatility squeeze is detected (BB width narrows relative to ATR).
*   **Entry Timing:** Can enter immediately upon confluence or wait for "Deceleration" (tick speed dropping by a specified percentage from its peak).
*   **High-Impact News Filter:** Avoids entries around major news events using the built-in MQL5 economic calendar.

## 3. Trade Management & Exits
The EA employs highly dynamic, proactive trade management rather than relying solely on static take-profits.

*   **Dynamic Take Profit (TP):** Defaults to reverting to the M1 Bollinger Band mean or half-mean.
*   **Momentum Hold:** If the entry was triggered by a spike and subsequent candle structure shows strong momentum (no opposing closes or engulfing patterns), it ignores the standard TP and holds until price reaches the opposite Bollinger Band extreme.
*   **Break of Structure (BOS) Risk Manager:** Tracks the extreme of the entry structure. If price breaks this structure and retests it against the position, the EA will exit early to mitigate risk.
*   **Slow Crawl Exit:** Cuts trades early if the price action is slowly grinding against the position, identified via consecutive adverse slopes on a fast EMA.
*   **Stop Loss:** Volatility-based using an ATR multiplier.

## 4. Key Insights & Development Notes
*   **SMC + Indicators Hybrid:** The bot effectively bridges the gap between algorithmic indicator logic and price-action/SMC concepts. The real-time liquidity scanner is a standout feature.
*   **Highly Defensive:** The strategy is extremely picky. It requires macro alignment, mid-level zoning, premium/discount verification, a liquidity sweep, structural clearance, and an absence of news. This likely results in a low frequency of high-probability setups.
*   **State-Driven Dashboard:** The extensive variables prefixed with `d_` (dashboard states) indicate a robust state machine that drives both the UI and the entry logic, making debugging and live monitoring exceptionally transparent.
*   **Adaptive Volatility:** The integration of ATR in almost all aspects (SL, Spikes, Squeezes, BOS buffers, Sweeps) ensures the bot scales its logic to current market conditions rather than relying on fixed point/pip values.