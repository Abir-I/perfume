# Shop Product Deduplication Fix

## Problem
The Shop API returned one card for every `Product` row. Since a single perfume can have multiple variants (5ml, 10ml, 20ml, full bottle), the same perfume appeared multiple times.

## Fix
The Shop API now:
1. Applies the existing filters and in-stock rule.
2. Orders matching variants by perfume, volume, then product ID.
3. Keeps only the first variant for each perfume.
4. Calculates the total count AFTER deduplication.
5. Applies pagination AFTER deduplication.
6. Leaves the perfume detail endpoint unchanged, so customers can still select/view all available sizes.

## UI
No visual/UI/UX changes were made.

## Representative variant
The smallest available matching volume is used for the Shop card. If the customer filters to a product type or other criteria, the representative is selected from the remaining matching variants.

## Tests added
- 5ml and 10ml of the same perfume produce one Shop card.
- Multiple variants of multiple perfumes produce one card per perfume.
- Empty product list returns empty.
