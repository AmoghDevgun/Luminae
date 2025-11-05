const mongoose = require('mongoose');

const scrapeResultSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  username: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['pending', 'running', 'completed', 'failed'],
    default: 'pending'
  },
  files: {
    postid: String,
    mediaIds: String,
    comments: String,
    likes: String,
    followers: String,
    leads: String,
    leadsData: String,
    leadsRanked: String
  },
  metadata: {
    totalLeads: Number,
    totalComments: Number,
    totalLikes: Number,
    totalFollowers: Number,
    startTime: Date,
    endTime: Date
  },
  error: String
}, {
  timestamps: true
});

// Index for faster queries
scrapeResultSchema.index({ user: 1, createdAt: -1 });

module.exports = mongoose.model('ScrapeResult', scrapeResultSchema);

