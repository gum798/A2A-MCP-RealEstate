const express = require('express');
const sampleData = require('../data/sampleData');

const router = express.Router();

// 모든 샘플 데이터 조회
router.get('/', (req, res) => {
  res.json({
    message: 'Sample data endpoints',
    availableTypes: Object.keys(sampleData),
    endpoints: [
      '/api/data/users',
      '/api/data/orders',
      '/api/data/products',
      '/api/data/system'
    ]
  });
});

// 사용자 데이터
router.get('/users', (req, res) => {
  res.json({
    type: 'user_data',
    data: sampleData.users,
    timestamp: new Date().toISOString()
  });
});

// 주문 데이터
router.get('/orders', (req, res) => {
  res.json({
    type: 'order_data',
    data: sampleData.orders,
    timestamp: new Date().toISOString()
  });
});

// 상품 데이터
router.get('/products', (req, res) => {
  res.json({
    type: 'product_data',
    data: sampleData.products,
    timestamp: new Date().toISOString()
  });
});

// 시스템 상태 데이터
router.get('/system', (req, res) => {
  res.json({
    type: 'system_data',
    data: sampleData.systemStatus,
    timestamp: new Date().toISOString()
  });
});

// 특정 타입 데이터 요청
router.get('/type/:dataType', (req, res) => {
  const { dataType } = req.params;
  
  if (sampleData[dataType]) {
    res.json({
      type: dataType,
      data: sampleData[dataType],
      timestamp: new Date().toISOString()
    });
  } else {
    res.status(404).json({
      error: 'Data type not found',
      availableTypes: Object.keys(sampleData)
    });
  }
});

// 샘플 데이터 생성 (POST)
router.post('/generate/:dataType', (req, res) => {
  const { dataType } = req.params;
  const { count = 5 } = req.body;
  
  const generateSampleData = (type, count) => {
    const generators = {
      users: () => Array.from({ length: count }, (_, i) => ({
        id: i + 100,
        name: `Generated User ${i + 1}`,
        email: `user${i + 1}@generated.com`,
        createdAt: new Date().toISOString()
      })),
      orders: () => Array.from({ length: count }, (_, i) => ({
        orderId: `GEN${String(i + 1).padStart(3, '0')}`,
        amount: Math.round((Math.random() * 1000 + 10) * 100) / 100,
        status: ['pending', 'completed', 'cancelled'][Math.floor(Math.random() * 3)],
        createdAt: new Date().toISOString()
      })),
      products: () => Array.from({ length: count }, (_, i) => ({
        id: i + 1000,
        name: `Generated Product ${i + 1}`,
        price: Math.round((Math.random() * 500 + 10) * 100) / 100,
        category: ['Electronics', 'Clothing', 'Books', 'Home'][Math.floor(Math.random() * 4)],
        stock: Math.floor(Math.random() * 100)
      }))
    };
    
    return generators[type] ? generators[type]() : null;
  };
  
  const generatedData = generateSampleData(dataType, count);
  
  if (generatedData) {
    res.json({
      type: dataType,
      count: generatedData.length,
      data: generatedData,
      timestamp: new Date().toISOString()
    });
  } else {
    res.status(400).json({
      error: 'Invalid data type for generation',
      supportedTypes: ['users', 'orders', 'products']
    });
  }
});

module.exports = router;