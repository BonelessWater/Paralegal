import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  Button,
} from '@mui/material';
import {
  Email as EmailIcon,
  Message as MessageIcon,
  Phone as PhoneIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  HourglassEmpty as HourglassEmptyIcon,
  PlayArrow as PlayArrowIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { mockOutreach } from '../mockData';

const OutreachMonitor: React.FC = () => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <EmailIcon />;
      case 'sms':
        return <MessageIcon />;
      case 'voice':
        return <PhoneIcon />;
      default:
        return <EmailIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'email':
        return '#2196f3';
      case 'sms':
        return '#4caf50';
      case 'voice':
        return '#9c27b0';
      default:
        return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircleIcon fontSize="small" />;
      case 'failed':
        return <CancelIcon fontSize="small" />;
      case 'sent':
        return <HourglassEmptyIcon fontSize="small" />;
      default:
        return <ScheduleIcon fontSize="small" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'success';
      case 'failed':
        return 'error';
      case 'sent':
        return 'info';
      default:
        return 'default';
    }
  };

  const emailsSent = mockOutreach.filter(o => o.type === 'email').length;
  const smsDelivered = mockOutreach.filter(o => o.type === 'sms' && o.status === 'delivered').length;
  const voiceCalls = mockOutreach.filter(o => o.type === 'voice').length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          Sent Items
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track all automated communications
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: 3,
          mb: 4,
        }}
      >
        <Card sx={{ bgcolor: '#e3f2fd', borderLeft: '4px solid #2196f3' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Emails Sent
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, color: '#2196f3', mt: 1 }}>
                  {emailsSent}
                </Typography>
              </Box>
              <Box
                sx={{
                  bgcolor: '#2196f320',
                  p: 2,
                  borderRadius: 2,
                  color: '#2196f3',
                }}
              >
                <EmailIcon sx={{ fontSize: 32 }} />
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ bgcolor: '#e8f5e9', borderLeft: '4px solid #4caf50' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  SMS Delivered
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, color: '#4caf50', mt: 1 }}>
                  {smsDelivered}
                </Typography>
              </Box>
              <Box
                sx={{
                  bgcolor: '#4caf5020',
                  p: 2,
                  borderRadius: 2,
                  color: '#4caf50',
                }}
              >
                <MessageIcon sx={{ fontSize: 32 }} />
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ bgcolor: '#f3e5f5', borderLeft: '4px solid #9c27b0' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Voice Calls
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, color: '#9c27b0', mt: 1 }}>
                  {voiceCalls}
                </Typography>
              </Box>
              <Box
                sx={{
                  bgcolor: '#9c27b020',
                  p: 2,
                  borderRadius: 2,
                  color: '#9c27b0',
                }}
              >
                <PhoneIcon sx={{ fontSize: 32 }} />
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Outreach Activities */}
      <Stack spacing={2}>
        {mockOutreach.map((activity) => (
          <Card
            key={activity.id}
            sx={{
              '&:hover': {
                boxShadow: 3,
                transform: 'translateY(-2px)',
                transition: 'all 0.2s',
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
                    bgcolor: `${getTypeColor(activity.type)}15`,
                    color: getTypeColor(activity.type),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {getTypeIcon(activity.type)}
                </Box>

                {/* Content */}
                <Box sx={{ flex: 1 }}>
                  {/* Header Row */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {activity.type.toUpperCase()}
                      </Typography>
                      <Chip
                        icon={getStatusIcon(activity.status)}
                        label={activity.status.toUpperCase()}
                        size="small"
                        color={getStatusColor(activity.status) as any}
                        sx={{ fontWeight: 600 }}
                      />
                    </Stack>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ScheduleIcon fontSize="inherit" />
                      {new Date(activity.timestamp).toLocaleString()}
                    </Typography>
                  </Box>

                  {/* Recipient */}
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <PersonIcon fontSize="small" />
                    To: {activity.recipient}
                  </Typography>

                  {/* Message Content */}
                  <Box
                    sx={{
                      bgcolor: '#f5f5f5',
                      border: '1px solid #e0e0e0',
                      borderRadius: 1,
                      p: 2,
                      mb: 2,
                    }}
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {activity.content}
                    </Typography>
                  </Box>

                  {/* Voice Recording Button */}
                  {activity.type === 'voice' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<PlayArrowIcon />}
                        sx={{
                          borderColor: '#9c27b0',
                          color: '#9c27b0',
                          '&:hover': { bgcolor: '#9c27b010', borderColor: '#9c27b0' },
                        }}
                      >
                        Play Recording
                      </Button>
                      <Typography variant="caption" color="text.secondary">
                        Generated by ElevenLabs Voice AI
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {/* Multi-Modal Info Card */}
      <Card
        sx={{
          mt: 4,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
            Multi-Modal Outreach
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
              gap: 3,
            }}
          >
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
                Email
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                SendGrid / AWS SES
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Professional correspondence
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
                SMS
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Twilio SMS API
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Quick client updates
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.8, mb: 1 }}>
                Voice
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                ElevenLabs + Twilio Voice
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                Automated appointment reminders
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default OutreachMonitor;
