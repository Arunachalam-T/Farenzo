const mongoose = require('mongoose');

const PredictionSchema = new mongoose.Schema({
  routeId: { type: mongoose.Schema.Types.ObjectId, ref: 'Route', required: true },
  fromCity: { type: String, required: true },
  toCity: { type: String, required: true },
  journeyDate: { type: Date, required: true },
  predictedFare: { type: Number, required: true },
  currentFare: { type: Number, required: true },
  confidence: { type: Number },
  recommendation: { type: String, enum: ['WAIT', 'BOOK_NOW', 'BOOK_SOON'] },
  recommendReason: { type: String },
  modelUsed: { type: String }
}, { timestamps: true });

module.exports = mongoose.model('Prediction', PredictionSchema);
