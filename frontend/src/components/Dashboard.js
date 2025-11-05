import React from 'react';
import { Link } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
  const { user } = useAuth();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Welcome back, {user?.username}!
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Start Scraping
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start a new Instagram scraping job and watch results stream in real-time.
                The scraper will collect profile posts, comments, likes, followers, and leads.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={Link} to="/scrape" variant="contained">
                Start Scraping
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                View Results
              </Typography>
              <Typography variant="body2" color="text.secondary">
                View all your previous scraping results. Download files and analyze the data
                collected from Instagram profiles.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={Link} to="/results" variant="contained">
                View Results
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;

