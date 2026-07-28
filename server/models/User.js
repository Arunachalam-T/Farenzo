const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, enum: ['user', 'admin'], default: 'user' },
  preferences: {
    notifyEmail: { type: Boolean, default: true },
    notifySMS: { type: Boolean, default: false }
  },
  lastLogin: { type: Date }
}, { timestamps: true });

// Never return password in queries by default
UserSchema.methods.toJSON = function() {
  const user = this.toObject();
  delete user.password;
  return user;
}

module.exports = mongoose.model('User', UserSchema);
