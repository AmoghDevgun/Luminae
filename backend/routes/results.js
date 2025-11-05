const express = require('express');
const fs = require('fs');
const path = require('path');
const ScrapeResult = require('../models/ScrapeResult');
const { protect } = require('../middleware/auth');

const router = express.Router();

// @route   GET /api/results
// @desc    Get all scrape results for current user
// @access  Private
router.get('/', protect, async (req, res) => {
  try {
    const results = await ScrapeResult.find({ user: req.user._id })
      .sort({ createdAt: -1 })
      .select('-__v');

    res.json({
      success: true,
      count: results.length,
      data: results
    });
  } catch (error) {
    console.error('Get results error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error' 
    });
  }
});

// @route   GET /api/results/:id/file/:fileKey
// @desc    Get file content for a scrape result
// @access  Private
router.get('/:id/file/:fileKey', protect, async (req, res) => {
  try {
    const result = await ScrapeResult.findById(req.params.id);

    if (!result) {
      return res.status(404).json({ 
        success: false, 
        message: 'Result not found' 
      });
    }

    // Check if user owns this result
    if (result.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ 
        success: false, 
        message: 'Not authorized to access this result' 
      });
    }

    const fileKey = req.params.fileKey;
    const filePath = result.files?.[fileKey];

    if (!filePath || !fs.existsSync(filePath)) {
      return res.status(404).json({ 
        success: false, 
        message: 'File not found' 
      });
    }

    // Read and send file content
    const fileContent = fs.readFileSync(filePath, 'utf8');
    res.send(fileContent);
  } catch (error) {
    console.error('Get file error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error' 
    });
  }
});

// @route   GET /api/results/:id
// @desc    Get single scrape result
// @access  Private
router.get('/:id', protect, async (req, res) => {
  try {
    const result = await ScrapeResult.findById(req.params.id);

    if (!result) {
      return res.status(404).json({ 
        success: false, 
        message: 'Result not found' 
      });
    }

    // Check if user owns this result
    if (result.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ 
        success: false, 
        message: 'Not authorized to access this result' 
      });
    }

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Get result error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error' 
    });
  }
});

// @route   DELETE /api/results/:id
// @desc    Delete scrape result
// @access  Private
router.delete('/:id', protect, async (req, res) => {
  try {
    const result = await ScrapeResult.findById(req.params.id);

    if (!result) {
      return res.status(404).json({ 
        success: false, 
        message: 'Result not found' 
      });
    }

    // Check if user owns this result
    if (result.user.toString() !== req.user._id.toString()) {
      return res.status(403).json({ 
        success: false, 
        message: 'Not authorized to delete this result' 
      });
    }

    await result.deleteOne();

    res.json({
      success: true,
      message: 'Result deleted successfully'
    });
  } catch (error) {
    console.error('Delete result error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error' 
    });
  }
});

module.exports = router;

