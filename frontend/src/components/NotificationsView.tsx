import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotifications } from '../contexts/NotificationContext';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  IconButton,
  Avatar,
  Divider,
  Button,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  MarkEmailRead as MarkEmailReadIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Flag as FlagIcon,
} from '@mui/icons-material';

const NotificationsView: React.FC = () => {
  const navigate = useNavigate();
  const { notifications, unreadCount, markAsRead, markAllAsRead, deleteNotification, clearAll } = useNotifications();

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'approval':
        return '#ff9800';
      case 'task':
        return '#2196f3';
      case 'message':
        return '#4caf50';
      case 'system':
        return '#9c27b0';
      default:
        return '#757575';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'approval':
        return '⚠️';
      case 'task':
        return '✓';
      case 'message':
        return '💬';
      case 'system':
        return '⚙️';
      default:
        return '📌';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          Notifications
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<MarkEmailReadIcon />}
          size="small"
          onClick={markAllAsRead}
        >
          Mark All as Read
        </Button>
        <Button
          variant="outlined"
          startIcon={<DeleteIcon />}
          size="small"
          color="error"
          onClick={clearAll}
        >
          Clear All
        </Button>
      </Stack>

      {/* Notifications List */}
      <Stack spacing={2}>
        {notifications.map((notification) => (
          <Card
            key={notification.id}
            onClick={() => {
              markAsRead(notification.id);
              notification.navigateTo && navigate(notification.navigateTo);
            }}
            sx={{
              bgcolor: notification.read ? 'background.paper' : '#f5f5f5',
              border: !notification.read ? '2px solid' : '1px solid',
              borderColor: !notification.read ? getTypeColor(notification.type) : 'divider',
              cursor: 'pointer',
              '&:hover': {
                boxShadow: 3,
                transform: 'translateY(-2px)',
                transition: 'all 0.2s',
                bgcolor: notification.read ? '#fafafa' : '#f0f0f0',
              },
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                {/* Icon */}
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    bgcolor: `${getTypeColor(notification.type)}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                  }}
                >
                  {getTypeIcon(notification.type)}
                </Box>

                {/* Content */}
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {notification.title}
                        {!notification.read && (
                          <Chip
                            label="NEW"
                            size="small"
                            color="error"
                            sx={{ ml: 1, height: 20, fontSize: '0.7rem', fontWeight: 700 }}
                          />
                        )}
                        {notification.priority === 'high' && (
                          <FlagIcon sx={{ ml: 1, fontSize: '1rem', color: 'error.main', verticalAlign: 'middle' }} />
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                    </Box>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent card click
                        deleteNotification(notification.id);
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                    <Chip
                      label={notification.type.toUpperCase()}
                      size="small"
                      sx={{
                        bgcolor: `${getTypeColor(notification.type)}15`,
                        color: getTypeColor(notification.type),
                        fontWeight: 600,
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ScheduleIcon fontSize="inherit" />
                      {notification.timestamp}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Box>
  );
};

export default NotificationsView;
