const express = require('express');
const router = express.Router();
const Route = require('../models/Route');

// GET /api/routes
// Get all active routes
router.get('/', async (req, res) => {
  try {
    const routes = await Route.find({ isActive: true }).sort({ fromCity: 1 });
    res.json({ count: routes.length, routes });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/routes/:id
// Get a single route by ID
router.get('/:id', async (req, res) => {
  try {
    const route = await Route.findById(req.params.id);
    if (!route) return res.status(404).json({ message: 'Route not found' });
    res.json(route);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/routes
// Create a new route
router.post('/', async (req, res) => {
  try {
    const { fromCity, toCity, fromCityId, toCityId, distanceKm } = req.body;

    // Prevent duplicate routes
    const existing = await Route.findOne({
      fromCity: new RegExp(`^${fromCity}$`, 'i'),
      toCity: new RegExp(`^${toCity}$`, 'i')
    });

    if (existing) {
      return res.status(400).json({ message: 'Route already exists', route: existing });
    }

    const route = await Route.create({ fromCity, toCity, fromCityId, toCityId, distanceKm });
    res.status(201).json(route);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/routes/:id
// Deactivate a route (soft delete)
router.delete('/:id', async (req, res) => {
  try {
    const route = await Route.findByIdAndUpdate(
      req.params.id,
      { isActive: false },
      { new: true }
    );
    if (!route) return res.status(404).json({ message: 'Route not found' });
    res.json({ message: 'Route deactivated', route });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
