import React, { useState, useRef, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';
import getApiUrl from '../config/api';

function Scraper() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [dataItems, setDataItems] = useState({
    postid: [],
    mediaIds: [],
    comments: [],
    likes: [],
    followers: [],
    leads: [],
    leadsData: [],
    leadsRanked: []
  });
  const [status, setStatus] = useState('idle'); // idle, running, completed, error
  const [error, setError] = useState('');
  const eventSourceRef = useRef(null);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleStart = async () => {
    if (!username.trim()) {
      setError('Please enter an Instagram username');
      return;
    }

    setLoading(true);
    setStatus('running');
    setLogs([]);
    setDataItems({
      postid: [],
      mediaIds: [],
      comments: [],
      likes: [],
      followers: [],
      leads: [],
      leadsData: [],
      leadsRanked: []
    });
    setError('');

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const token = localStorage.getItem('token');
      
      // Use fetch with POST for streaming
      const response = await fetch(getApiUrl('api/scrape/start'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ username: username.trim() })
      });

      if (!response.ok) {
        throw new Error('Failed to start scraping');
      }

      // Read the stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const readStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
              setStatus('completed');
              setLoading(false);
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  handleStreamData(data);
                } catch (e) {
                  // Ignore parse errors
                }
              }
            }
          }
        } catch (error) {
          console.error('Stream error:', error);
          setError('Error reading stream');
          setStatus('error');
          setLoading(false);
        }
      };

      readStream();
      eventSourceRef.current = { close: () => reader.cancel() };
    } catch (error) {
      console.error('Start scraping error:', error);
      setError(error.message || 'Failed to start scraping');
      setStatus('error');
      setLoading(false);
    }
  };

  const handleStreamData = (data) => {
    switch (data.type) {
      case 'connected':
        setLogs(prev => [...prev, { type: 'info', message: data.message }]);
        break;
      
      case 'log':
        setLogs(prev => [...prev, { type: 'log', message: data.message }]);
        break;
      
      case 'error':
        setLogs(prev => [...prev, { type: 'error', message: data.message }]);
        break;
      
      case 'data':
        if (data.file && data.data) {
          setDataItems(prev => ({
            ...prev,
            [data.file]: [...prev[data.file], data.data]
          }));
        }
        break;
      
      case 'complete':
        setStatus(data.code === 0 ? 'completed' : 'error');
        setLoading(false);
        setLogs(prev => [...prev, { 
          type: data.code === 0 ? 'info' : 'error', 
          message: data.message 
        }]);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        break;
      
      default:
        break;
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setLoading(false);
    setStatus('idle');
    setLogs(prev => [...prev, { type: 'info', message: 'Scraping stopped by user' }]);
  };

  const getFileCount = (key) => {
    return dataItems[key]?.length || 0;
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Instagram Scraper
        </Typography>

        <Box sx={{ mt: 3, mb: 3 }}>
          <TextField
            fullWidth
            label="Instagram Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter Instagram username (without @)"
            disabled={loading}
            sx={{ mb: 2 }}
          />
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={handleStart}
              disabled={loading || !username.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Scraping...' : 'Start Scraping'}
            </Button>
            
            {loading && (
              <Button
                variant="outlined"
                color="error"
                onClick={handleStop}
              >
                Stop
              </Button>
            )}
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {status === 'completed' && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Scraping completed successfully!
          </Alert>
        )}

        {status === 'error' && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Scraping failed. Check logs for details.
          </Alert>
        )}

        {/* Statistics */}
        <Box sx={{ mt: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Statistics
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip label={`Posts: ${getFileCount('postid')}`} color="primary" />
            <Chip label={`Comments: ${getFileCount('comments')}`} color="primary" />
            <Chip label={`Likes: ${getFileCount('likes')}`} color="primary" />
            <Chip label={`Followers: ${getFileCount('followers')}`} color="primary" />
            <Chip label={`Leads: ${getFileCount('leads')}`} color="secondary" />
            <Chip label={`Leads Data: ${getFileCount('leadsData')}`} color="secondary" />
            <Chip label={`Ranked Leads: ${getFileCount('leadsRanked')}`} color="secondary" />
          </Box>
        </Box>

        {/* Data Sections */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Collected Data
          </Typography>
          {Object.entries(dataItems).map(([key, items]) => {
            if (items.length === 0) return null;
            
            const displayName = key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1').trim();
            
            return (
              <Accordion key={key} sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mr: 2 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {displayName}
                    </Typography>
                    <Chip label={`${items.length} items`} size="small" color="primary" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {key === 'comments' || key === 'leadsData' || key === 'leadsRanked' ? (
                    // Table view for structured data
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            {key === 'comments' && (
                              <>
                                <TableCell>Username</TableCell>
                                <TableCell>Comment</TableCell>
                                <TableCell>Likes</TableCell>
                              </>
                            )}
                            {key === 'leadsData' && (
                              <>
                                <TableCell>Username</TableCell>
                                <TableCell>Full Name</TableCell>
                                <TableCell>Followers</TableCell>
                                <TableCell>Following</TableCell>
                              </>
                            )}
                            {key === 'leadsRanked' && (
                              <>
                                <TableCell>Username</TableCell>
                                <TableCell>Score</TableCell>
                                <TableCell>Category</TableCell>
                                <TableCell>Followers</TableCell>
                              </>
                            )}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {items.map((item, index) => (
                            <TableRow key={index}>
                              {key === 'comments' && (
                                <>
                                  <TableCell>{item.username || '-'}</TableCell>
                                  <TableCell>{item.text?.substring(0, 50) || '-'}...</TableCell>
                                  <TableCell>{item.likes || 0}</TableCell>
                                </>
                              )}
                              {key === 'leadsData' && (
                                <>
                                  <TableCell>{item.username || '-'}</TableCell>
                                  <TableCell>{item.full_name || '-'}</TableCell>
                                  <TableCell>{item.follower_count?.toLocaleString() || 0}</TableCell>
                                  <TableCell>{item.following_count?.toLocaleString() || 0}</TableCell>
                                </>
                              )}
                              {key === 'leadsRanked' && (
                                <>
                                  <TableCell>{item.username || '-'}</TableCell>
                                  <TableCell>
                                    <Chip 
                                      label={item.lead_score?.toFixed(2) || '0.00'} 
                                      size="small"
                                      color={item.lead_score > 0.7 ? 'success' : item.lead_score > 0.4 ? 'warning' : 'default'}
                                    />
                                  </TableCell>
                                  <TableCell>{item.category || '-'}</TableCell>
                                  <TableCell>{item.followers?.toLocaleString() || 0}</TableCell>
                                </>
                              )}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    // List view for simple data
                    <List dense>
                      {items.map((item, index) => (
                        <React.Fragment key={index}>
                          <ListItem>
                            <ListItemText
                              primary={String(item)}
                              secondary={`Item ${index + 1}`}
                            />
                          </ListItem>
                          {index < items.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>

        {/* Logs */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Logs
          </Typography>
          <Paper
            variant="outlined"
            sx={{
              maxHeight: 400,
              overflow: 'auto',
              p: 2,
              bgcolor: '#f5f5f5'
            }}
          >
            <List dense>
              {logs.map((log, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={log.message}
                    secondary={
                      <Chip
                        label={log.type}
                        size="small"
                        color={
                          log.type === 'error' ? 'error' :
                          log.type === 'info' ? 'success' : 'default'
                        }
                      />
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      </Paper>
    </Container>
  );
}

export default Scraper;

