const express = require('express');
const router = express.Router();
const perfumes = require('../data/perfumes.json');

/**
 * TASK 8: Product Browsing Feature
 * GET /api/products
 * Lists all perfumes. Supports filtering by:
 *   - brand   e.g. /api/products?brand=Dior
 *   - size    e.g. /api/products?size=10ml
 *   - type    e.g. /api/products?type=decant   (or "full bottle")
 * Filters can be combined, e.g. /api/products?brand=Creed&type=decant
 */
router.get('/', (req, res) => {
  let results = perfumes;
  const { brand, size, type } = req.query;

  if (brand) {
    results = results.filter(
      (p) => p.brand.toLowerCase() === brand.toLowerCase()
    );
  }

  if (size) {
    results = results.filter((p) =>
      p.sizes.some((s) => s.toLowerCase() === size.toLowerCase())
    );
  }

  if (type) {
    results = results.filter(
      (p) => p.type.toLowerCase() === type.toLowerCase()
    );
  }

  res.json({
    count: results.length,
    products: results,
  });
});

module.exports = router;
