import { AppBar, Toolbar, IconButton, Typography, Box, Avatar, Menu, MenuItem, Chip, Breadcrumbs, Link as MuiLink } from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  NavigateNext as NavigateNextIcon,
} from '@mui/icons-material';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useNotifications } from '../contexts/NotificationContext';

const pageNames: Record<string, string> = {
  '/': 'Dashboard',
  '/inbox': 'Inbox',
  '/approval': 'Approval Queue',
  '/agents': 'AI Agents',
  '/outreach': 'Outreach Monitor',
  '/notifications': 'Notifications',
  '/settings': 'Settings',
  '/profile': 'Profile',
};

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { unreadCount } = useNotifications();
  const currentPage = pageNames[location.pathname] || 'Dashboard';
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleProfileClick = () => {
    handleMenuClose();
    navigate('/profile');
  };

  const handleSettingsClick = () => {
    handleMenuClose();
    navigate('/settings');
  };

  const handleLogout = () => {
    handleMenuClose();
    // Add logout logic here
    alert('Logout functionality would be implemented here');
  };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: 'secondary.main',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: 2 }}>
        {/* Breadcrumbs */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          {/* Breadcrumbs */}
          <Breadcrumbs
            separator={<NavigateNextIcon fontSize="small" sx={{ color: 'rgba(255, 255, 255, 0.5)' }} />}
            sx={{ display: { xs: 'none', md: 'flex' } }}
          >
            <MuiLink
              component={Link}
              to="/"
              underline="hover"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                '&:hover': { color: 'white' },
                fontSize: '0.875rem',
              }}
            >
              Home
            </MuiLink>
            <Typography sx={{ color: 'white', fontSize: '0.875rem', fontWeight: 500 }}>
              {currentPage}
            </Typography>
          </Breadcrumbs>
        </Box>

        {/* Firm Info */}
        <Box sx={{ display: { xs: 'none', lg: 'block' }, mr: 3 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: 'white',
              textAlign: 'right',
              fontSize: '0.875rem',
            }}
          >
            Morgan & Morgan
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'rgba(255, 255, 255, 0.7)',
              textAlign: 'right',
              display: 'block',
              fontSize: '0.75rem',
            }}
          >
            Personal Injury Division
          </Typography>
        </Box>

        {/* Notifications */}
        <IconButton
          color="inherit"
          onClick={() => navigate('/notifications')}
          sx={{
            mr: 1,
            position: 'relative',
          }}
        >
          <NotificationsIcon />
          {unreadCount > 0 && (
            <Chip
              label={unreadCount}
              size="small"
              sx={{
                position: 'absolute',
                top: 4,
                right: 4,
                height: 18,
                minWidth: 18,
                fontSize: '0.7rem',
                fontWeight: 700,
                bgcolor: 'error.main',
                color: 'white',
                '& .MuiChip-label': {
                  px: 0.5,
                },
              }}
            />
          )}
        </IconButton>

        {/* Settings */}
        <IconButton 
          color="inherit" 
          sx={{ mr: 1 }}
          onClick={() => navigate('/settings')}
        >
          <SettingsIcon />
        </IconButton>

        {/* User Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton
            onClick={handleMenuOpen}
            sx={{
              p: 0,
              border: '2px solid',
              borderColor: 'primary.main',
            }}
          >
            <Avatar
              sx={{
                bgcolor: 'primary.main',
                width: 38,
                height: 38,
                fontSize: '0.95rem',
                fontWeight: 700,
              }}
            >
              JD
            </Avatar>
          </IconButton>

          <Box sx={{ ml: 1.5, display: { xs: 'none', md: 'block' } }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: 'white',
                lineHeight: 1.2,
                fontSize: '0.875rem',
              }}
            >
              John Doe
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.75rem',
              }}
            >
              Senior Paralegal
            </Typography>
          </Box>
        </Box>

        {/* User Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          sx={{ mt: 1 }}
        >
          <MenuItem onClick={handleProfileClick}>Profile</MenuItem>
          <MenuItem onClick={handleProfileClick}>My Account</MenuItem>
          <MenuItem onClick={handleSettingsClick}>Settings</MenuItem>
          <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
