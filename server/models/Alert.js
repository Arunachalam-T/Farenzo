const mongoose = require('mongoose');

const AlertSchema = new mongoose.Schema({
  userId: { type: String, required: true },
  routeId: { type: mongoose.Schema.Types.ObjectId, ref: 'Route', required: true },
  fromCity: { type: String, required: true },
  toCity: { type: String, required: true },
  journeyDate: { type: Date, required: true },
  targetPrice: { type: Number, required: true },
  currentPrice: { type: Number },
  status: { type: String, enum: ['active', 'triggered', 'expired'], default: 'active' },
  notifiedAt: { type: Date }
}, { timestamps: true });

module.exports = mongoose.model('Alert', AlertSchema);
