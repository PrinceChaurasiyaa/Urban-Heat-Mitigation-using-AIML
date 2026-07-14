# Urban Heat Mitigation Project — Explained in Plain English

## The Story

Imagine you're the municipal commissioner of Delhi.

People keep complaining:

- Roads are too hot to walk on.
- Buildings trap heat and never cool down at night.
- Some neighborhoods are 5°C hotter than others, just a few kilometers apart.
- Electricity demand keeps rising because everyone runs their AC all day.

The government turns to you and asks four simple questions:

1. Where should we plant trees?
2. Which buildings should get cool roofs?
3. Where should we build parks or lakes?
4. How much will the temperature actually drop if we do this?

This project is built to answer exactly those four questions — with data, not guesswork.

---

## Step 1 — Find the Hot Places

The first job is simple: **which places are actually hot?**

We use satellites for this. A satellite called Landsat can measure the **Land Surface Temperature (LST)** — basically, how hot the ground itself is, not the air.

| Location | LST |
|---|---|
| Park | 29°C |
| Residential area | 33°C |
| Industrial area | 41°C |
| Highway | 44°C |

We turn these numbers into a color-coded map:

- 🔵 Blue → Cool
- 🟡 Yellow → Warm
- 🔴 Red → Very hot

This map is called a **Heat Stress Map** — it shows exactly where the hotspots are.

**✔ Output 1: Heat Stress Map**

---

## Step 2 — Figure Out WHY a Place Is Hot

Knowing a place is hot isn't enough. The AI now asks: *why* is this industrial area sitting at 44°C?

Possible reasons:

- No trees nearby
- Concrete roads everywhere
- Too many closely packed buildings
- Black/dark rooftops that absorb heat
- No water body nearby to cool the air

To capture this, we calculate a set of measurable "features" for every location:

- **NDVI** — how much vegetation is present
- **NDBI** — how "built-up" (concrete/buildings) the area is
- **NDWI** — how much water is nearby
- **Building density** — how packed the buildings are
- **Road density** — how much road surface exists
- **Humidity, wind speed, air temperature** — weather conditions
- **Sky View Factor** — how much open sky is visible from ground level (tall buildings block it)

Every single point on the map ends up with its own set of numbers. For example:

**Pixel A**
- Temperature = 42°C
- NDVI = 0.08 (almost no vegetation)
- NDBI = 0.79 (heavily built-up)
- Humidity = 38%
- Wind = 1.2 m/s
- Building density = High

These numbers become the **inputs** that we feed into the AI model.

---

## Step 3 — Train the AI

Now the AI learns the relationship between these features and temperature:

- More trees → temperature goes down
- More concrete → temperature goes up
- More humidity → temperature goes down (humid air holds and moves heat differently)

We start with a straightforward, well-understood AI model — something like **Random Forest** or **XGBoost** — as a baseline. This gives us a reliable first version before building something more advanced.

---

## Step 4 — Make the AI Explain Itself

A normal AI model just spits out a number:

> "Prediction: 41°C"

That's not good enough for a city planner. They need to know **why**.

For this, we use a technique called **SHAP**, which breaks down exactly how much each factor contributed to the final temperature. For example, SHAP might tell us:

| Factor | Contribution |
|---|---|
| Built-up area | +5°C |
| Low vegetation | +4°C |
| Roads | +2°C |
| Humidity | −1°C |

Now the government has a clear, specific answer:

> "This area is hot mainly because it has almost no vegetation."

This is called **Driver Attribution** — it tells you exactly what's driving the heat.

---

## Step 5 — Make the AI Physics-Aware (the most important part)

A normal AI model only learns patterns from data — it doesn't necessarily understand *how heat actually works*.

But cities obey the laws of physics. Heat energy follows a simple accounting rule called the **Surface Energy Balance**:

> Incoming solar energy = Heat stored + Heat lost to air + Heat lost to evaporation + Heat absorbed by the ground

Written more formally:

**Rn = H + LE + G**

Where:
- **Rn** = Net radiation (the incoming solar energy)
- **H** = Sensible heat (heat that warms the air directly)
- **LE** = Latent heat (cooling caused by evaporation — this is why trees and water cool an area)
- **G** = Ground heat (heat absorbed and stored by the surface itself)

Instead of only trying to minimize prediction error, we also penalize the model whenever it breaks this energy balance rule. This keeps the AI's predictions physically realistic — even in situations it hasn't seen before, like a brand-new tree-planting scenario with no historical precedent.

This hybrid approach is called **Physics-Informed AI**.

---

## Step 6 — Simulate Cooling Strategies (virtually, before spending a rupee)

This is the fun part. Say an area currently looks like this:

> Concrete, concrete, concrete — no trees anywhere.

The AI asks a "what if" question: *what if we planted 500 trees here?*

We simply change the vegetation number for that area:

- Old NDVI = 0.12
- New NDVI = 0.42 (simulating denser vegetation)

Then we run the trained model again on this new, hypothetical version of the area.

**Result:**
- Before: 42°C
- After: 37°C
- **Cooling effect: 5°C**

No tree is actually planted. Nothing is built. We are simply simulating the outcome using the model — a safe, free way to test ideas before committing money.

### More example scenarios

| Scenario | Intervention | Effect | Estimated cooling |
|---|---|---|---|
| 1 | Increase tree cover by 20% | More shade + evaporative cooling | ↓ 3°C |
| 2 | Cool (white) roofs | Reflects sunlight instead of absorbing it | ↓ 2°C |
| 3 | New water body (lake) | Evaporation cools surrounding air | ↓ 1.8°C |
| 4 | Combine all three (trees + cool roofs + lake) | Compounding effect | ↓ 6°C |

The system compares multiple strategies side by side, so planners can see the trade-offs before deciding.

---

## Step 7 — Optimize: Get the Most Cooling for the Money

Now suppose the city has a budget of ₹100 crore. It obviously can't plant trees everywhere or turn every roof white — money and space are limited.

This is where **optimization** comes in. The system searches through many possible combinations of interventions to find the one that gives the **most cooling for the available budget and space**.

Example candidates:

| Area | Intervention | Cooling effect |
|---|---|---|
| Area A | Plant trees | 3°C |
| Area B | Cool roofs | 2°C |
| Area C | New lake | 5°C |

The optimizer might conclude:

> **Best plan:** Trees in Area A + Cool roofs in Area B + Lake in Area C → Maximum overall cooling within budget.

Algorithms like **Genetic Algorithms** or **Simulated Annealing** are well suited to searching through this huge number of possible combinations efficiently.

---

## The Full Workflow, Start to Finish

```
Satellite images
      │
      ▼
Compute Land Surface Temperature (LST)
      │
      ▼
Find heat hotspots
      │
      ▼
Extract features
(vegetation, built-up area, water,
buildings, roads, humidity, wind...)
      │
      ▼
Train the AI model
      │
      ▼
Explain why each area is hot (SHAP)
      │
      ▼
Make the AI physics-aware
(Energy balance constraint)
      │
      ▼
Simulate cooling scenarios
(trees, cool roofs, water bodies, albedo)
      │
      ▼
Optimize under budget/space constraints
      │
      ▼
Best cooling strategy, with numbers attached
```

---

## What the Project Ultimately Delivers

- 🗺️ **Heat Stress Map** — showing exactly where the hotspots are
- 📊 **Driver analysis** — explaining *why* each hotspot is hot
- 🤖 **A validated, physics-informed AI model** — accurate and physically realistic
- 🌳 **Simulated cooling strategies** — tested virtually before real-world investment
- 📍 **Best intervention locations** — where to act first for maximum impact
- 🌡️ **Estimated temperature reduction** — e.g., "This intervention will reduce LST by 3.8°C"
- 📈 **An interactive dashboard and report** — so planners can explore results themselves

In short: the system turns "it feels hot here" into "here's exactly where, why, and what to do about it — with a number attached to the benefit."
