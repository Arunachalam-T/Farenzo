const express = require('express');
const router = express.Router();
const Prediction = require('../models/Prediction');
const Fare = require('../models/Fare');

// GET /api/predictions?from=Chennai&to=Bangalore&date=2026-08-01
// Get prediction for a route and date
router.get('/', async (req, res) => {
  try {
    const { from, to, date } = req.query;

    if (!from || !to || !date) {
      return res.status(400).json({ error: 'from, to, and date are required' });
    }

    const journeyDate = new Date(date);
    const nextDay = new Date(journeyDate);
    nextDay.setDate(nextDay.getDate() + 1);

    const prediction = await Prediction.findOne({
      fromCity: new RegExp(from, 'i'),
      toCity: new RegExp(to, 'i'),
      journeyDate: { $gte: journeyDate, $lt: nextDay }
    }).sort({ createdAt: -1 }); // most recent prediction

    if (!prediction) {
      return res.status(404).json({ message: 'No prediction available for this route/date yet' });
    }

    res.json(prediction);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/predictions/generate
// Generate a simple rule-based prediction from existing fare data
// Body: { routeId, fromCity, toCity, journeyDate }
router.post('/generate', async (req, res) => {
  try {
    const { routeId, fromCity, toCity, journeyDate } = req.body;

    if (!routeId || !fromCity || !toCity || !journeyDate) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    const targetDate = new Date(journeyDate);

    // Get recent fare data for this route
    const recentFares = await Fare.find({
      fromCity: new RegExp(fromCity, 'i'),
      toCity: new RegExp(toCity, 'i')
    }).sort({ recordedAt: -1 }).limit(50);

    if (recentFares.length === 0) {
      return res.status(404).json({ message: 'Not enough fare data to generate prediction' });
    }

    // Calculate stats from historical data
    const fareValues = recentFares.map(f => f.fare);
    const avgFare = fareValues.reduce((a, b) => a + b, 0) / fareValues.length;
    const currentFare = fareValues[0]; // most recent fare

    // Rule-based recommendation logic
    const daysUntilJourney = Math.ceil((targetDate - new Date()) / (1000 * 60 * 60 * 24));
    const isWeekend = [0, 6].includes(targetDate.getDay());

    let recommendation;
    let recommendReason;
    let confidence;

    if (currentFare < avgFare * 0.85) {
      recommendation = 'BOOK_NOW';
      recommendReason = `Current fare (₹${currentFare}) is 15%+ below average (₹${Math.round(avgFare)}). Great deal!`;
      confidence = 85;
    } else if (daysUntilJourney <= 2) {
      recommendation = 'BOOK_NOW';
      recommendReason = 'Journey is in 2 days or less. Prices typically rise close to departure.';
      confidence = 90;
    } else if (isWeekend && daysUntilJourney > 5) {
      recommendation = 'WAIT';
      recommendReason = 'Weekend journey but still 5+ days away. Fares may drop mid-week.';
      confidence = 65;
    } else if (currentFare > avgFare * 1.15) {
      recommendation = 'WAIT';
      recommendReason = `Current fare (₹${currentFare}) is 15%+ above average (₹${Math.round(avgFare)}). Wait for a price drop.`;
      confidence = 75;
    } else {
      recommendation = 'BOOK_SOON';
      recommendReason = `Fare is near average (₹${Math.round(avgFare)}). Book within the next 2 days.`;
      confidence = 70;
    }

    // Save prediction to DB
    const prediction = await Prediction.create({
      routeId,
      fromCity,
      toCity,
      journeyDate: targetDate,
      predictedFare: Math.round(avgFare),
      currentFare,
      confidence,
      recommendation,
      recommendReason,
      modelUsed: 'rule-based-v1'
    });

    res.status(201).json({ message: '🤖 Prediction generated!', prediction });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
