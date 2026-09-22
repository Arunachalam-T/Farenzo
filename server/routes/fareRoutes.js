const express = require('express');
const router = express.Router();
const Fare = require('../models/Fare');

// GET /api/fares?from=Chennai&to=Bangalore&date=2026-08-01
// Search fares by route and date
router.get('/', async (req, res) => {
  try {
    const { from, to, date } = req.query;

    if (!from || !to || !date) {
      return res.status(400).json({ error: 'from, to, and date are required query params' });
    }

    const journeyDate = new Date(date);
    const nextDay = new Date(journeyDate);
    nextDay.setDate(nextDay.getDate() + 1);

    const fares = await Fare.find({
      fromCity: new RegExp(from, 'i'),
      toCity: new RegExp(to, 'i'),
      journeyDate: { $gte: journeyDate, $lt: nextDay }
    }).sort({ fare: 1 }); // cheapest first

    res.json({ count: fares.length, fares });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/fares/history?from=Chennai&to=Bangalore
// Get fare history for a route (for price trend chart)
router.get('/history', async (req, res) => {
  try {
    const { from, to } = req.query;

    if (!from || !to) {
      return res.status(400).json({ error: 'from and to are required' });
    }

    const history = await Fare.aggregate([
      {
        $match: {
          fromCity: new RegExp(from, 'i'),
          toCity: new RegExp(to, 'i')
        }
      },
      {
        $group: {
          _id: { $dateToString: { format: '%Y-%m-%d', date: '$recordedAt' } },
          avgFare: { $avg: '$fare' },
          minFare: { $min: '$fare' },
          maxFare: { $max: '$fare' },
          count: { $sum: 1 }
        }
      },
      { $sort: { _id: 1 } },
      { $limit: 30 } // last 30 data points
    ]);

    res.json({ route: `${from} → ${to}`, history });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/fares/cheapest?from=Chennai&to=Bangalore&date=2026-08-01
// Get the single cheapest fare for a route
router.get('/cheapest', async (req, res) => {
  try {
    const { from, to, date } = req.query;

    if (!from || !to || !date) {
      return res.status(400).json({ error: 'from, to, and date are required' });
    }

    const journeyDate = new Date(date);
    const nextDay = new Date(journeyDate);
    nextDay.setDate(nextDay.getDate() + 1);

    const cheapest = await Fare.findOne({
      fromCity: new RegExp(from, 'i'),
      toCity: new RegExp(to, 'i'),
      journeyDate: { $gte: journeyDate, $lt: nextDay }
    }).sort({ fare: 1 });

    if (!cheapest) {
      return res.status(404).json({ message: 'No fares found for this route and date' });
    }

    res.json(cheapest);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
