const express = require('express');
const router = express.Router();
const perfumes = require('../data/perfumes.json');

/**
 * TASK 10: Brand List Feature
 * GET /api/brands
 * Returns the full, de-duplicated, alphabetically sorted list of brands
 * carried by the store — for use in filters and menus.
 */
router.get('/', (req, res) => {
  const brands = [...new Set(perfumes.map((p) => p.brand))].sort();
  res.json({ brands });
});

module.exports = router;
