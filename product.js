const express = require('express');
const router = express.Router();
const perfumes = require('../data/perfumes.json');

/**
 * TASK 9: Single Product Page Feature
 * GET /api/products/:id
 * Returns all details for one specific perfume: brand, notes, price, sizes, etc.
 */
router.get('/:id', (req, res) => {
  const id = parseInt(req.params.id, 10);
  const product = perfumes.find((p) => p.id === id);

  if (!product) {
    return res.status(404).json({ error: 'Product not found' });
  }

  res.json(product);
});

module.exports = router;
