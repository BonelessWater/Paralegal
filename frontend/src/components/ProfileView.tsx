import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Stack,
  Switch,
  FormControlLabel,
  Divider,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Palette as PaletteIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
} from '@mui/icons-material';

const ProfileView: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          My Profile
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your account settings and preferences
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
        {/* Profile Information */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Profile Information
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Avatar
                sx={{
                  bgcolor: '#8a6d4f',
                  width: 80,
                  height: 80,
                  fontSize: '2rem',
                  fontWeight: 700,
                  mr: 2,
                }}
              >
                JD
              </Avatar>
              <Button variant="outlined" size="small">
                Change Photo
              </Button>
            </Box>

            <Stack spacing={2}>
              <TextField
                fullWidth
                label="Full Name"
                defaultValue="John Doe"
                variant="outlined"
              />
              <TextField
                fullWidth
                label="Job Title"
                defaultValue="Senior Paralegal"
                variant="outlined"
              />
              <TextField
                fullWidth
                label="Email"
                defaultValue="john.doe@morganandmorgan.com"
                type="email"
                variant="outlined"
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
              <TextField
                fullWidth
                label="Phone"
                defaultValue="+1 (555) 123-4567"
                variant="outlined"
                InputProps={{
                  startAdornment: <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                sx={{
                  bgcolor: '#8a6d4f',
                  '&:hover': { bgcolor: '#6d5640' },
                }}
              >
                Save Changes
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Preferences
            </Typography>

            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <NotificationsIcon fontSize="small" />
                  Notifications
                </Typography>
                <Stack spacing={1}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Email notifications"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Desktop notifications"
                  />
                  <FormControlLabel
                    control={<Switch />}
                    label="SMS notifications"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Approval alerts"
                  />
                </Stack>
              </Box>

              <Divider />

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PaletteIcon fontSize="small" />
                  Display
                </Typography>
                <Stack spacing={1}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Dark mode"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Compact view"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Show avatars"
                  />
                </Stack>
              </Box>

              <Divider />

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SecurityIcon fontSize="small" />
                  Security
                </Typography>
                <Stack spacing={1}>
                  <Button variant="outlined" fullWidth>
                    Change Password
                  </Button>
                  <Button variant="outlined" fullWidth>
                    Two-Factor Authentication
                  </Button>
                  <Button variant="outlined" fullWidth color="error">
                    Sign Out All Devices
                  </Button>
                </Stack>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Workspace Info */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Workspace Information
            </Typography>

            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Law Firm
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  Morgan & Morgan
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Division
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  Personal Injury Division
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Office Location
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  Atlanta, GA
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Member Since
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  January 2023
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card sx={{ bgcolor: '#f5f5f5' }}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Your Performance
            </Typography>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'white', borderRadius: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#2196f3' }}>
                  247
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Tasks Completed
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'white', borderRadius: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#4caf50' }}>
                  98%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Approval Rate
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'white', borderRadius: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#ff9800' }}>
                  3.2h
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'white', borderRadius: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#9c27b0' }}>
                  42
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Active Clients
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default ProfileView;
