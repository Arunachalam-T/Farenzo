const mongoose = require('mongoose');

const RouteSchema = new mongoose.Schema({
  fromCity: { type: String, required: true },
  toCity: { type: String, required: true },
  fromCityId: { type: Number },
  toCityId: { type: Number },
  distanceKm: { type: Number },
  avgFare: { type: Number },
  isActive: { type: Boolean, default: true }
}, { timestamps: true });

module.exports = mongoose.model('Route', RouteSchema);
