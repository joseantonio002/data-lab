
# Data modeling and dashboard for a public transport company

This course project designs the first iteration of a Business Intelligence (BI) initiative for a public bus operator (TITSA, Tenerife). The deliverable is a set of business objectives, critical success factors, and indicators, translated into a multidimensional data model and a Power BI dashboard aimed at short-term operational decision-making.

Primary reference documents:
- Assignment brief: `business_intelligence/TITSA_modeling/requirements_assignment.pdf`
- Final report: `business_intelligence/TITSA_modeling/INInformeFinal.pdf`

## Problem and approach (how the assignment is solved)

The problem is to go from "business strategy" to "actionable dashboards" by:
1) describing the business and decomposing it into business areas,
2) expressing strategy as objectives -> CSFs (Critical Success Factors) -> indicators (PI),
3) designing a logical (multidimensional) data warehouse model that can compute those indicators,
4) implementing a dashboard for one selected business process.

In this project the company is decomposed into three core areas:
- Planning (service offering, punctuality, occupancy)
- Technical workshop management (fleet maintenance + inventory)
- Driver management (shifts, coverage, compliance)

Then, for each area:
- Define the area objective.
- Define at least one CSF that makes the objective measurable.
- Define indicators with: description, type, goal/target (meta), and the action the business would take if the indicator is off.

Finally:
- Pick the main business processes that best support the indicators with a rich dimensional model.
- Define fact tables, grain, refresh rate, measures (including additivity), and dimensions (including SCD strategy and special modeling techniques).
- Build a dashboard for a single process (here: trips) aligned with a real user persona.

## What the final report contains

### 1) Business context
TITSA is presented as a public transport operator (large fleet, many lines, high ridership). Because it is public, the "north star" is service quality and sustainability rather than profit maximization.

### 2) Business objectives, CSFs, and indicators
The report defines 5 CSFs and 19 indicators (IDs) across the three areas.

Planning area (objective: offer a high-quality service):
- CSF1: Service punctuality
  - ID1 % of punctual trips (within +/- 5 minutes) - KPI - goal: >= 90% and non-decreasing week-to-week
  - ID2 % of "severe delay" trips (>15 minutes) - KPI - goal: <= 1%
  - ID3 Avg arrival delay (minutes) - RI - goal: reduce vs previous year
  - ID4 Avg departure delay (minutes) - RI - goal: reduce vs previous year
- CSF2: Service quality aligned with demand
  - ID5 Avg occupancy (%) - KPI - goal: <= 75% on working days
  - ID6 % saturated trips (occupancy > 90%) - KRI - goal: reduce vs previous year
  - ID7 Schedule compliance (% trips operated vs planned) - KRI - goal: >= 99.5%
  - ID8 Within-trip passenger variability (%) (max vs min passengers) - KRI - goal: reduce vs previous year

Technical workshop area (objective: keep enough stock while minimizing inventory value; repair vehicles fast):
- CSF3: Inventory management
  - ID9 Total spare-parts inventory value per workshop - KPI
  - ID10 % of inventory value in critical (ABC "A") components - KPI
  - ID11 Critical components with zero stock - KPI
  - ID12 % inventory value in "no movement in 12 months" components - KRI
  - ID13 Component stockout-risk proxy using recent in/out and current stock - KRI
- CSF4: Bus repairs
  - ID14 Mean repair time - KPI
  - ID15 % fleet available - KPI
  - ID16 % rework (repeat repair within 30 days) - KRI

Driver management area (objective: cover services while respecting labor agreements):
- CSF5: Shift management
  - ID17 % planned services covered with an assigned driver - KPI
  - ID18 % overtime hours - RI
  - ID19 % regulatory/compliance violations in shift planning - KRI

Modeling scope note (explicit in the report): only two business processes are modeled in the logical design, so indicators ID14-ID19 are marked as "process not modeled" in the computation table.

### 3) Logical (multidimensional) design
Two fact tables are designed:
- Trips fact ("Viajes en guagua"): transactional fact at trip grain; refresh in near real-time.
- Inventory fact ("Gestion del inventario"): periodic snapshot at (component, workshop, day) grain; refresh daily.

Key modeling decisions and BI techniques highlighted in the report:
- Snowflake schema (not a pure star) with normalized dimensions where it better matches the business.
- SCD handling:
  - Type 2 (new row per change) for entities where historical context matters (e.g., stops, vehicles, parts classification).
  - Type 4 (separate history table) for employees: keep current state for analysis while storing a detailed audit-like history elsewhere.
- Special dimensions:
- Bridge dimension between itineraries and stops to handle a "set of stops per itinerary" relationship that changes over time.
  - Outrigger dimension (supplier) hanging off parts.
  - Separated Date and Time dimensions (Calendar + Time) to avoid an overly large combined time dimension.
- Measure additivity discussion (additive vs semi-additive vs non-additive), especially relevant for snapshot inventory measures.

### 4) Data exploitation: dashboard
The implemented dashboard is built in Power BI for the Planning department, focused on the Trips process and indicators ID1-ID8.

Design choices described in the report:
- Target user: Planning team (technical users, used to tabular analysis).
- Purpose: monthly review to detect lines/time slots with punctuality or capacity issues and decide actions (schedule adjustment, reinforcement, capacity changes).
- Update cadence: monthly "push" of aggregated data.
- Global filters: time slot (franja horaria) and day type (laboral/no laboral).
- Visuals:
  - Area charts for global incident percentages (delays, severe delays, not-operated, saturation).
  - Top-5 ranking tables to prioritize worst-performing lines.
  - Bar chart comparing departure vs arrival delay by line.

## BI concepts used (glossary aligned with the report)

- Objective: the desired business outcome for an area (e.g., "offer a high-quality service").
- CSF (Critical Success Factor): a small set of conditions that must go well to achieve the objective; CSFs turn strategy into something you can manage.
- Indicator (PI): a measurable definition used to track a CSF. Each indicator should be specific about scope, time window, and how it is computed.
- Indicator types (as used in the report):
  - KPI (Key Performance Indicator): tracks performance against a target (goal) and is used to steer actions.
  - KRI (Key Risk Indicator): tracks risk/exceptions that threaten the CSF; it is often "alarm-like" (e.g., saturation, non-compliance).
  - RI (Result Indicator): outcome/lagging measure that reflects the result of operations (e.g., average delay times, overtime share).
- Goal / Target ("Meta"): the desired threshold or direction (>=, <=, reduce by X, keep within a range) for an indicator.
- Action: the operational response when an indicator deviates from the goal (e.g., adjust schedules, change fleet allocation, rebalance inventory).

## How to open the dashboard

- Open `business_intelligence/TITSA_modeling/dashboard.pbix` with Power BI Desktop.
- If you only want to view the result, open `business_intelligence/TITSA_modeling/dashboard.pdf`.
