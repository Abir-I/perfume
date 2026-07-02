const express = require('express');
const app = express();

const productsRouter = require('./routes/products');   // Task 8
const productRouter = require('./routes/product');      // Task 9
const brandsRouter = require('./routes/brands');         // Task 10

app.use(express.json());

app.use('/api/products', productsRouter); // GET /api/products?brand=&size=&type=
app.use('/api/products', productRouter);  // GET /api/products/:id
app.use('/api/brands', brandsRouter);     // GET /api/brands

app.get('/', (req, res) => {
  res.send('Perfume Store API is running. Try /api/products, /api/products/1, /api/brands');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Perfume API listening on port ${PORT}`);
});

module.exports = app;
