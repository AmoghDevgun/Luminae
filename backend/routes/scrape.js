const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const ScrapeResult = require('../models/ScrapeResult');
const { protect } = require('../middleware/auth');

const router = express.Router();

// @route   POST /api/scrape/start
// @desc    Start scraping and stream results
// @access  Private
router.post('/start', protect, (req, res) => {
  const { username } = req.body;

  if (!username) {
    return res.status(400).json({ 
      success: false, 
      message: 'Instagram username is required' 
    });
  }

  // Set up Server-Sent Events
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  // Send initial connection message
  res.write(`data: ${JSON.stringify({ type: 'connected', message: 'Streaming started' })}\n\n`);

  // Create scrape result record
  ScrapeResult.create({
    user: req.user._id,
    username: username,
    status: 'running',
    metadata: { startTime: new Date() }
  }).then(scrapeResult => {
    // Path to main.py
    const mainScriptPath = path.join(__dirname, '../../main.py');
    const outputDir = path.join(__dirname, '../../output');

    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Stream data from Python script
    // Pass username as stdin to avoid interactive input
    const pythonProcess = spawn('python3', [mainScriptPath], {
      cwd: path.join(__dirname, '../..'),
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Send username to Python script stdin
    pythonProcess.stdin.write(username + '\n');
    pythonProcess.stdin.end();

    let stdoutBuffer = '';
    let stderrBuffer = '';

    // Handle stdout (Python print statements)
    pythonProcess.stdout.on('data', (data) => {
      stdoutBuffer += data.toString();
      const lines = stdoutBuffer.split('\n');
      stdoutBuffer = lines.pop() || ''; // Keep incomplete line

      lines.forEach(line => {
        if (line.trim()) {
          res.write(`data: ${JSON.stringify({ 
            type: 'log', 
            message: line.trim() 
          })}\n\n`);
        }
      });
    });

    // Handle stderr
    pythonProcess.stderr.on('data', (data) => {
      stderrBuffer += data.toString();
      const lines = stderrBuffer.split('\n');
      stderrBuffer = lines.pop() || '';

      lines.forEach(line => {
        if (line.trim()) {
          res.write(`data: ${JSON.stringify({ 
            type: 'error', 
            message: line.trim() 
          })}\n\n`);
        }
      });
    });

    // Monitor output files and stream results
    const filesToMonitor = [
      { key: 'postid', file: `${username}_postid.txt` },
      { key: 'mediaIds', file: `${username}_media_ids.txt` },
      { key: 'comments', file: `${username}_comments.json` },
      { key: 'likes', file: `${username}_likers.txt` },
      { key: 'followers', file: `${username}_followers.txt` },
      { key: 'leads', file: `${username}_leads.txt` },
      { key: 'leadsData', file: `${username}_leads_data.json` },
      { key: 'leadsRanked', file: `${username}_leads_ranked.json` }
    ];

    const filePositions = new Map(); // Track read position for each file
    const fileStreams = new Map(); // Track active streams to avoid duplicates

    // Monitor files every 2 seconds
    const monitorInterval = setInterval(() => {
      filesToMonitor.forEach(({ key, file }) => {
        const filePath = path.join(outputDir, file);
        
        if (fs.existsSync(filePath)) {
          const stats = fs.statSync(filePath);
          const currentSize = stats.size;
          const lastPosition = filePositions.get(key) || 0;
          
          // Only process if file has new content and we're not already streaming it
          if (currentSize > lastPosition && !fileStreams.has(key)) {
            // File has new content, stream it
            streamFileIncremental(filePath, key, lastPosition, res, scrapeResult._id, filePositions, fileStreams);
          }
        }
      });
    }, 2000); // Check every 2 seconds

    // Stream incremental file content
    function streamFileIncremental(filePath, fileKey, startPosition, response, resultId, filePositionsMap, fileStreamsMap) {
      try {
        if (!fs.existsSync(filePath)) return;

        // Mark that we're streaming this file
        fileStreamsMap.set(fileKey, true);

        const fileExtension = path.extname(filePath);
        const stream = fs.createReadStream(filePath, { 
          encoding: 'utf8',
          start: startPosition
        });
        
        let buffer = '';
        let bytesRead = 0;

        stream.on('data', (chunk) => {
          buffer += chunk;
          bytesRead += Buffer.byteLength(chunk, 'utf8');
          
          if (fileExtension === '.json') {
            // Parse JSON items from buffer - handle streamed JSON arrays
            // Look for complete JSON objects (may span multiple lines)
            let jsonBuffer = buffer;
            
            // Try to extract complete JSON objects
            let braceCount = 0;
            let objectStart = -1;
            let inString = false;
            let escapeNext = false;
            
            for (let i = 0; i < jsonBuffer.length; i++) {
              const char = jsonBuffer[i];
              
              if (escapeNext) {
                escapeNext = false;
                continue;
              }
              
              if (char === '\\') {
                escapeNext = true;
                continue;
              }
              
              if (char === '"' && !escapeNext) {
                inString = !inString;
                continue;
              }
              
              if (!inString) {
                if (char === '{') {
                  if (braceCount === 0) {
                    objectStart = i;
                  }
                  braceCount++;
                } else if (char === '}') {
                  braceCount--;
                  if (braceCount === 0 && objectStart >= 0) {
                    // Found complete object
                    try {
                      const jsonStr = jsonBuffer.substring(objectStart, i + 1);
                      const item = JSON.parse(jsonStr);
                      response.write(`data: ${JSON.stringify({
                        type: 'data',
                        file: fileKey,
                        data: item
                      })}\n\n`);
                      
                      // Remove processed object from buffer
                      jsonBuffer = jsonBuffer.substring(i + 1);
                      i = -1; // Reset to start
                      objectStart = -1;
                    } catch (e) {
                      // Invalid JSON, skip
                    }
                  }
                }
              }
            }
            
            // Keep unprocessed buffer (incomplete objects)
            buffer = jsonBuffer;
          } else {
            // Text file - stream line by line
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            lines.forEach(line => {
              if (line.trim()) {
                response.write(`data: ${JSON.stringify({
                  type: 'data',
                  file: fileKey,
                  data: line.trim()
                })}\n\n`);
              }
            });
          }
        });

        stream.on('end', () => {
          // Update position after we've finished reading
          filePositionsMap.set(fileKey, startPosition + bytesRead);
          // Remove from active streams
          fileStreamsMap.delete(fileKey);
        });

        stream.on('error', (error) => {
          console.error(`Stream error for ${filePath}:`, error);
          fileStreamsMap.delete(fileKey);
        });

        // Update scrape result with file path
        ScrapeResult.findByIdAndUpdate(resultId, {
          $set: { [`files.${fileKey}`]: filePath }
        }).exec();
        
      } catch (error) {
        console.error(`Error streaming file ${filePath}:`, error);
        fileStreamsMap.delete(fileKey);
      }
    }

    // Handle process completion
    pythonProcess.on('close', (code) => {
      // Clean up monitoring interval
      clearInterval(monitorInterval);

      // Final read of any remaining content - wait a bit for files to finish writing
      setTimeout(() => {
        filesToMonitor.forEach(({ key, file }) => {
          const filePath = path.join(outputDir, file);
          if (fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath);
            const lastPosition = filePositions.get(key) || 0;
            const currentSize = stats.size;
            
            // Read all remaining content
            if (currentSize > lastPosition) {
              // Read the entire remaining portion
              const remainingContent = fs.readFileSync(filePath, 'utf8').slice(lastPosition);
              
              if (remainingContent.trim()) {
                const fileExtension = path.extname(filePath);
                
                if (fileExtension === '.json') {
                  // Parse JSON items - extract complete JSON objects
                  let braceCount = 0;
                  let objectStart = -1;
                  let inString = false;
                  let escapeNext = false;
                  
                  for (let i = 0; i < remainingContent.length; i++) {
                    const char = remainingContent[i];
                    
                    if (escapeNext) {
                      escapeNext = false;
                      continue;
                    }
                    
                    if (char === '\\') {
                      escapeNext = true;
                      continue;
                    }
                    
                    if (char === '"' && !escapeNext) {
                      inString = !inString;
                      continue;
                    }
                    
                    if (!inString) {
                      if (char === '{') {
                        if (braceCount === 0) {
                          objectStart = i;
                        }
                        braceCount++;
                      } else if (char === '}') {
                        braceCount--;
                        if (braceCount === 0 && objectStart >= 0) {
                          // Found complete object
                          try {
                            const jsonStr = remainingContent.substring(objectStart, i + 1);
                            const item = JSON.parse(jsonStr);
                            res.write(`data: ${JSON.stringify({
                              type: 'data',
                              file: key,
                              data: item
                            })}\n\n`);
                          } catch (e) {
                            // Invalid JSON, skip
                          }
                          objectStart = -1;
                        }
                      }
                    }
                  }
                } else {
                  // Text file - send line by line
                  const lines = remainingContent.split('\n');
                  lines.forEach(line => {
                    if (line.trim()) {
                      res.write(`data: ${JSON.stringify({
                        type: 'data',
                        file: key,
                        data: line.trim()
                      })}\n\n`);
                    }
                  });
                }
              }
              
              // Update position
              filePositions.set(key, currentSize);
            }
          }
        });
        
        // Send completion message after final read
        res.write(`data: ${JSON.stringify({ 
          type: 'complete', 
          code: code,
          message: code === 0 ? 'Scraping completed successfully' : 'Scraping failed'
        })}\n\n`);
        
        res.end();
      }, 3000); // Wait 3 seconds for all files to finish writing

      // Update scrape result (will be updated again after final read)
      ScrapeResult.findByIdAndUpdate(scrapeResult._id, {
        status: code === 0 ? 'completed' : 'failed',
        'metadata.endTime': new Date(),
        error: code !== 0 ? `Process exited with code ${code}` : undefined
      }).exec();
    });

    // Handle client disconnect
    req.on('close', () => {
      pythonProcess.kill();
      clearInterval(monitorInterval);
      ScrapeResult.findByIdAndUpdate(scrapeResult._id, {
        status: 'failed',
        error: 'Client disconnected'
      }).exec();
    });

  }).catch(error => {
    console.error('Error creating scrape result:', error);
    res.write(`data: ${JSON.stringify({ 
      type: 'error', 
      message: 'Failed to start scraping process' 
    })}\n\n`);
    res.end();
  });
});

module.exports = router;

