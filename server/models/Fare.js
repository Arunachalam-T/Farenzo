const mongoose = require('mongoose');

const FareSchema = new mongoose.Schema({
  routeId: { type: mongoose.Schema.Types.ObjectId, ref: 'Route', required: true },
  fromCity: { type: String, required: true },
  toCity: { type: String, required: true },
  operator: { type: String, required: true },
  busType: { type: String, required: true },
  departureTime: { type: String, required: true },
  arrivalTime: { type: String, required: true },
  durationMins: { type: Number },
  fare: { type: Number, required: true },
  originalFare: { type: Number },
  seatsAvailable: { type: Number },
  source: { type: String, enum: ['redbus', 'abhibus'], required: true },
  journeyDate: { type: Date, required: true },
  recordedAt: { type: Date, default: Date.now },
  daysBeforeJourney: { type: Number },
  isWeekend: { type: Boolean, default: false },
  isHoliday: { type: Boolean, default: false }
});

module.exports = mongoose.model('Fare', FareSchema);
