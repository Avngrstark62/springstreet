Great. At this point you've basically built the data model. Now let's define the **business logic**.

---

# Factsheet

A factsheet is mostly a collection of aggregations over the holdings.

Suppose:

```text
AAPL 45%
AMZN 15%
CSK  40%
```

---

## 1. Top Holdings

Just the holdings themselves.

```text
AAPL 45%
CSK  40%
AMZN 15%
```

Sort by weight descending.

No formula.

---

## 2. Sector Exposure

Each holding belongs to a sector.

Example:

```text
AAPL -> Technology
AMZN -> Consumer Cyclical
CSK  -> Unknown
```

Exposure = sum of holding weights per sector.

Formula:

```text
Sector Exposure(S)
=
Σ(weight of holdings in sector S)
```

Example:

```text
Technology         = 45%
Consumer Cyclical  = 15%
Unknown            = 40%
```

Must sum to 100%.

---

## 3. Country Exposure

Same idea.

```text
AAPL -> United States
AMZN -> United States
CSK  -> Unknown
```

Formula:

```text
Country Exposure(C)
=
Σ(weight of holdings in country C)
```

Example:

```text
United States = 60%
Unknown       = 40%
```

---

## 4. Market Cap Exposure

Each stock has:

```text
market_cap
```

Convert it into a bucket.

Example:

```text
Large Cap : > 10B
Mid Cap   : 2B-10B
Small Cap : < 2B
```

Then:

```text
Market Cap Exposure(B)
=
Σ(weight of holdings in bucket B)
```

Example:

```text
Large Cap = 60%
Unknown   = 40%
```

---

## 5. Number of Holdings

Formula:

```text
count(holdings)
```

Example:

```text
3
```

---

## 6. Largest Holding

Formula:

```text
argmax(weight)
```

Example:

```text
AAPL (45%)
```

---

# Performance

This is the interesting part.

---

## Individual Stock Return

Suppose:

```text
Today Price = 120

30 Days Ago Price = 100
```

Return:

```text
(120 - 100) / 100
=
20%
```

Formula:

```text
Return
=
(Current Price - Old Price)
/
Old Price
```

---

## Portfolio Return

Prisma is a weighted combination of stocks.

Example:

```text
AAPL return = 20%
weight = 45%

AMZN return = 10%
weight = 15%

CSK return = 5%
weight = 40%
```

Portfolio Return:

```text
=
45% × 20%
+
15% × 10%
+
40% × 5%
```

Formula:

```text
Portfolio Return
=
Σ(weight × stock_return)
```

This is the most important formula in the whole assignment.

---

## 1 Month Performance

For each stock:

```text
Return_1M
=
(Current Close)
/
(Close 30 Days Ago)
-
1
```

Portfolio:

```text
Σ(weight × Return_1M)
```

---

## 3 Month Performance

Same formula.

Just use:

```text
Close 90 days ago
```

instead.

---

## 1 Year Performance

Same formula.

Use:

```text
Close 365 days ago
```

---

# Performance Chart

Imagine:

```text
Day 1
Day 2
Day 3
...
```

For every day:

Calculate portfolio value.

---

Example

Initial portfolio:

```text
100 units
```

Day 1:

```text
AAPL +1%
AMZN +2%
CSK +0%
```

Portfolio:

```text
45×1%
+
15×2%
+
40×0%

=
0.75%
```

Portfolio value:

```text
100 -> 100.75
```

Store:

```text
Day 1 -> 100.75
```

Repeat for every day.

The chart is simply:

```text
date -> portfolio value
```

---

# Therefore

## Factsheet Route

Uses:

```text
holdings
+
securities
```

Calculates:

```text
Top Holdings
Sector Exposure
Country Exposure
Market Cap Exposure
Number of Holdings
Largest Holding
```

---

## Performance Route

Uses:

```text
holdings
+
price_history
```

Calculates:

```text
1M Return
3M Return
1Y Return

Portfolio Growth Chart
```

using the core formula:

```text
Portfolio Return
=
Σ(weight × stock_return)
```

That's essentially the entire mathematical foundation behind your backend. Everything else is just data fetching and formatting.

{
  "product": {
    "id": "5dec7503-bea2-46fa-98ae-418512d2ffc9",
    "name": "Global Growth Prisma",
    "slug": "global-growth-prisma",
    "description": "Global equity portfolio"
  },

  "summary": {
    "holdings_count": 3,
    "largest_holding": {
      "ticker": "AAPL",
      "weight": 45.0
    }
  },

  "top_holdings": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "weight": 45.0
    },
    {
      "ticker": "CSK",
      "company_name": "76871",
      "weight": 40.0
    },
    {
      "ticker": "AMZN",
      "company_name": "Amazon.com, Inc.",
      "weight": 15.0
    }
  ],

  "sector_exposure": [
    {
      "sector": "Technology",
      "weight": 45.0
    },
    {
      "sector": "Consumer Cyclical",
      "weight": 15.0
    },
    {
      "sector": "Unknown",
      "weight": 40.0
    }
  ],

  "country_exposure": [
    {
      "country": "United States",
      "weight": 60.0
    },
    {
      "country": "Unknown",
      "weight": 40.0
    }
  ],

  "market_cap_exposure": [
    {
      "bucket": "Large Cap",
      "weight": 60.0
    },
    {
      "bucket": "Unknown",
      "weight": 40.0
    }
  ],

  "last_updated": "2026-06-03T17:39:43Z"
}
