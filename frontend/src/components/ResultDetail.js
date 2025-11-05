import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import axios from 'axios';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function ResultDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [fileData, setFileData] = useState({});

  useEffect(() => {
    fetchResult();
  }, [id]);

  const fetchResult = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/results/${id}`);
      setResult(response.data.data);
      
      // Fetch file contents
      if (response.data.data.files) {
        await fetchFileContents(response.data.data.files);
      }
    } catch (error) {
      setError('Failed to fetch result details');
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFileContents = async (files) => {
    const data = {};
    
    for (const [key, filePath] of Object.entries(files)) {
      if (!filePath) continue;
      
      try {
        // Read file from backend
        const response = await axios.get(`/api/results/${id}/file/${key}`, {
          responseType: 'text'
        });
        
        if (filePath.endsWith('.json')) {
          try {
            data[key] = JSON.parse(response.data);
          } catch (e) {
            data[key] = response.data;
          }
        } else {
          data[key] = response.data.split('\n').filter(line => line.trim());
        }
      } catch (error) {
        console.error(`Error fetching file ${key}:`, error);
        data[key] = [];
      }
    }
    
    setFileData(data);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const renderTable = (items, columns) => {
    if (!items || items.length === 0) {
      return <Typography color="text.secondary">No data available</Typography>;
    }

    return (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key}><strong>{col.label}</strong></TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {items.slice(0, 100).map((item, index) => (
              <TableRow key={index}>
                {columns.map((col) => (
                  <TableCell key={col.key}>
                    {col.render ? col.render(item) : String(item[col.key] || '-')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {items.length > 100 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
            Showing 100 of {items.length} items
          </Typography>
        )}
      </TableContainer>
    );
  };

  const renderComments = () => {
    const comments = Array.isArray(fileData.comments) ? fileData.comments : [];
    return renderTable(comments, [
      { key: 'username', label: 'Username' },
      { key: 'text', label: 'Comment', render: (item) => (item.text || '').substring(0, 100) },
      { key: 'likes', label: 'Likes', render: (item) => item.likes?.toLocaleString() || 0 }
    ]);
  };

  const renderLeadsData = () => {
    const leads = Array.isArray(fileData.leadsData) ? fileData.leadsData : [];
    return renderTable(leads, [
      { key: 'username', label: 'Username' },
      { key: 'full_name', label: 'Full Name' },
      { key: 'follower_count', label: 'Followers', render: (item) => item.follower_count?.toLocaleString() || 0 },
      { key: 'following_count', label: 'Following', render: (item) => item.following_count?.toLocaleString() || 0 },
      { key: 'biography', label: 'Bio', render: (item) => (item.biography || '').substring(0, 50) }
    ]);
  };

  const renderLeadsRanked = () => {
    const ranked = Array.isArray(fileData.leadsRanked) ? fileData.leadsRanked : [];
    return renderTable(ranked, [
      { key: 'username', label: 'Username' },
      { 
        key: 'lead_score', 
        label: 'Score', 
        render: (item) => (
          <Chip 
            label={item.lead_score?.toFixed(2) || '0.00'} 
            size="small"
            color={item.lead_score > 0.7 ? 'success' : item.lead_score > 0.4 ? 'warning' : 'default'}
          />
        )
      },
      { key: 'category', label: 'Category' },
      { key: 'followers', label: 'Followers', render: (item) => item.followers?.toLocaleString() || 0 },
      { key: 'following', label: 'Following', render: (item) => item.following?.toLocaleString() || 0 }
    ]);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !result) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error || 'Result not found'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/results')} sx={{ mt: 2 }}>
          Back to Results
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/results')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Scraping Result: @{result.username}
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Status</Typography>
              <Chip 
                label={result.status} 
                color={
                  result.status === 'completed' ? 'success' :
                  result.status === 'running' ? 'warning' :
                  'error'
                }
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Start Time</Typography>
              <Typography variant="h6">
                {result.metadata?.startTime 
                  ? new Date(result.metadata.startTime).toLocaleString()
                  : '-'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>End Time</Typography>
              <Typography variant="h6">
                {result.metadata?.endTime 
                  ? new Date(result.metadata.endTime).toLocaleString()
                  : '-'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>Files</Typography>
              <Typography variant="h6">
                {Object.values(result.files || {}).filter(Boolean).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different data types */}
      <Paper elevation={3}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="Comments" />
          <Tab label="Leads Data" />
          <Tab label="Ranked Leads" />
          <Tab label="Post IDs" />
          <Tab label="Followers" />
          <Tab label="Likes" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {renderComments()}
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {renderLeadsData()}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {renderLeadsRanked()}
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {fileData.postid && fileData.postid.length > 0 ? (
            <List dense>
              {fileData.postid.slice(0, 100).map((item, index) => (
                <ListItem key={index}>
                  <ListItemText primary={String(item)} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">No post IDs available</Typography>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          {fileData.followers && fileData.followers.length > 0 ? (
            <List dense>
              {fileData.followers.slice(0, 100).map((item, index) => (
                <ListItem key={index}>
                  <ListItemText primary={String(item)} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">No followers data available</Typography>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={5}>
          {fileData.likes && fileData.likes.length > 0 ? (
            <List dense>
              {fileData.likes.slice(0, 100).map((item, index) => (
                <ListItem key={index}>
                  <ListItemText primary={String(item)} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">No likes data available</Typography>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
}

export default ResultDetail;

