const express = require('express');
const router = express.Router();
const perfumes = require('../data/perfumes.json');


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
