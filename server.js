const express = require('express');
const app = express();

const productsRouter = require('./routes/products');   
const productRouter = require('./routes/product');      
const brandsRouter = require('./routes/brands');         

app.use(express.json());

app.use('/api/products', productsRouter); 
app.use('/api/products', productRouter);  
app.use('/api/brands', brandsRouter);     

app.get('/', (req, res) => {
  res.send('Perfume Store API is running. Try /api/products, /api/products/1, /api/brands');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Perfume API listening on port ${PORT}`);
});

module.exports = app;
