const express = require('express');
const router = express.Router();
const perfumes = require('../data/perfumes.json');

router.get('/', (req, res) => {
  const brands = [...new Set(perfumes.map((p) => p.brand))].sort();
  res.json({ brands });
});

module.exports = router;
