require('dotenv').config();
const express = require('express');
const { v4: uuidv4 } = require('uuid');

const agentRoutes = require('./routes/agent');
const dataRoutes = require('./routes/data');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  const requestId = uuidv4();
  req.requestId = requestId;
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - Request ID: ${requestId}`);
  next();
});

// Routes
app.use('/api/agent', agentRoutes);
app.use('/api/data', dataRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    agent: {
      id: process.env.AGENT_ID,
      name: process.env.AGENT_NAME
    }
  });
});

// Default route
app.get('/', (req, res) => {
  res.json({
    message: 'A2A Agent Server',
    version: '1.0.0',
    endpoints: [
      '/health',
      '/api/agent/*',
      '/api/data/*'
    ]
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`A2A Agent server running on port ${PORT}`);
  console.log(`Agent ID: ${process.env.AGENT_ID}`);
  console.log(`Agent Name: ${process.env.AGENT_NAME}`);
});