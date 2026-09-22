const express = require('express');
const router = express.Router();
const Alert = require('../models/Alert');

// GET /api/alerts?userId=abc123
// Get all alerts for a user
router.get('/', async (req, res) => {
  try {
    const { userId } = req.query;
    if (!userId) return res.status(400).json({ error: 'userId is required' });

    const alerts = await Alert.find({ userId })
      .populate('routeId', 'fromCity toCity distanceKm')
      .sort({ createdAt: -1 });

    res.json({ count: alerts.length, alerts });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/alerts
// Create a new price alert
// Body: { userId, routeId, fromCity, toCity, journeyDate, targetPrice }
router.post('/', async (req, res) => {
  try {
    const { userId, routeId, fromCity, toCity, journeyDate, targetPrice } = req.body;

    if (!userId || !routeId || !fromCity || !toCity || !journeyDate || !targetPrice) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    const alert = await Alert.create({
      userId,
      routeId,
      fromCity,
      toCity,
      journeyDate: new Date(journeyDate),
      targetPrice
    });

    res.status(201).json({ message: '🔔 Alert created!', alert });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PATCH /api/alerts/:id
// Update target price for an alert
router.patch('/:id', async (req, res) => {
  try {
    const { targetPrice } = req.body;
    const alert = await Alert.findByIdAndUpdate(
      req.params.id,
      { targetPrice },
      { new: true }
    );
    if (!alert) return res.status(404).json({ message: 'Alert not found' });
    res.json({ message: 'Alert updated', alert });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/alerts/:id
// Delete an alert
router.delete('/:id', async (req, res) => {
  try {
    const alert = await Alert.findByIdAndDelete(req.params.id);
    if (!alert) return res.status(404).json({ message: 'Alert not found' });
    res.json({ message: '🗑️ Alert deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
