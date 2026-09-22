const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const connectDB = require('./config/db');

// Load env vars
dotenv.config();

// Connect to database
connectDB();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/fares',       require('./routes/fareRoutes'));
app.use('/api/routes',      require('./routes/routeRoutes'));
app.use('/api/alerts',      require('./routes/alertRoutes'));
app.use('/api/predictions', require('./routes/predictionRoutes'));

// Health check
app.get('/', (req, res) => {
  res.json({
    message: '🚌 Farenzo API is running!',
    endpoints: [
      'GET  /api/fares?from=&to=&date=',
      'GET  /api/fares/history?from=&to=',
      'GET  /api/fares/cheapest?from=&to=&date=',
      'GET  /api/routes',
      'POST /api/routes',
      'GET  /api/alerts?userId=',
      'POST /api/alerts',
      'DELETE /api/alerts/:id',
      'GET  /api/predictions?from=&to=&date=',
      'POST /api/predictions/generate',
    ]
  });
});

const PORT = process.env.PORT || 5000;

// Global error handler middleware
app.use((err, req, res, next) => {
  console.error('❌ Unhandled error:', err.message);
  res.status(500).json({ error: 'Internal server error', message: err.message });
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});

// Handle uncaught exceptions gracefully
process.on('unhandledRejection', (err) => {
  console.error('❌ Unhandled Promise Rejection:', err.message);
});
