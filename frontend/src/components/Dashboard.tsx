import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Tabs,
  Tab,
  Stack,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  ArrowForward as ArrowForwardIcon,
  Flag as FlagIcon,
  People as PeopleIcon,
  Sms as SmsIcon,
  Info as InfoIcon,
  CalendarToday as CalendarTodayIcon,
  Person as PersonIcon,
  FormatListNumbered as FormatListNumberedIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { getSystemStats, getTasks, type SystemStats, type Task as APITask } from '../services/api';
import { makeCall } from '../services/api';

interface Task {
  id: string;
  title: string;
  client: string;
  priority: 'high' | 'medium' | 'low';
  type: 'call' | 'email' | 'document' | 'review';
  dueDate: string;
  status: 'urgent' | 'pending' | 'completed';
  description?: string;
  caseNumber?: string;
  assignedTo?: string;
  lastUpdated?: string;
  nextSteps?: string[];
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState(0);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  
  // API State
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [apiTasks, setApiTasks] = useState<APITask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch system stats and tasks
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [statsData, tasksData] = await Promise.all([
          getSystemStats(),
          getTasks()
        ]);
        setStats(statsData);
        setApiTasks(tasksData);
        setError(null);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to connect to backend. Please ensure the API server is running.');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Poll every 10 seconds for updates
    const interval = setInterval(loadData, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const handleTakeAction = (task: Task) => {
    setSelectedTask(task);
    setActionDialogOpen(true);
  };

  const [actionBusy, setActionBusy] = useState(false);

  const handleActionSelect = async (actionType: 'email' | 'call' | 'text') => {
    if (!selectedTask) return;

    try {
      setActionBusy(true);

      if (actionType === 'call') {
        // Option A: let server use its DEFAULT_PHONE_NUMBER
        const resp = await makeCall(); 
        // Option B: pass a number if you have it on the task
        // const resp = await makeCall(selectedTask.clientPhone);

        console.log('Call started:', resp);
        alert(`📞 Call initiated${resp?.callSid ? ` (SID: ${resp.callSid})` : ''}`);
      } else if (actionType === 'email') {
        // TODO: integrate your /email endpoint
        alert(`(demo) Would send email to ${selectedTask.client}`);
      } else if (actionType === 'text') {
        // TODO: integrate your /text endpoint
        alert(`(demo) Would send SMS to ${selectedTask.client}`);
      }

      setActionDialogOpen(false);
      setSelectedTask(null);
    } catch (err: any) {
      console.error(err);
      alert(`❌ Failed to perform action: ${err?.message || err}`);
    } finally {
      setActionBusy(false);
    }
  };


  const handleCloseDialog = () => {
    setActionDialogOpen(false);
    setSelectedTask(null);
  };

  const handleViewDetails = (task: Task) => {
    setSelectedTask(task);
    setDetailsDialogOpen(true);
  };

  const handleCloseDetailsDialog = () => {
    setDetailsDialogOpen(false);
    setSelectedTask(null);
  };

  // Sample data - in production this would come from your backend
  const tasks: Task[] = [
    {
      id: '1',
      title: 'Follow up on Johnson contract',
      client: 'Johnson LLC',
      priority: 'high',
      type: 'call',
      dueDate: 'Today, 2:00 PM',
      status: 'urgent',
      description: 'Client requested urgent follow-up regarding contract amendments for the Q4 partnership agreement.',
      caseNumber: 'CASE-2025-1847',
      assignedTo: 'John Doe',
      lastUpdated: 'October 25, 2025 at 10:30 AM',
      nextSteps: [
        'Review amended contract terms',
        'Schedule call with client',
        'Prepare response memo',
        'Get partner approval'
      ],
    },
    {
      id: '2',
      title: 'Review Smith deposition documents',
      client: 'Smith & Associates',
      priority: 'high',
      type: 'review',
      dueDate: 'Today, 4:00 PM',
      status: 'urgent',
      description: 'Critical deposition documents need review before tomorrow\'s court hearing. Focus on exhibits 12-18.',
      caseNumber: 'CASE-2025-1923',
      assignedTo: 'John Doe',
      lastUpdated: 'October 25, 2025 at 9:15 AM',
      nextSteps: [
        'Review all deposition transcripts',
        'Verify exhibit authenticity',
        'Highlight key testimonies',
        'Prepare cross-examination notes'
      ],
    },
    {
      id: '3',
      title: 'Draft response to Chen inquiry',
      client: 'Chen Industries',
      priority: 'medium',
      type: 'email',
      dueDate: 'Tomorrow',
      status: 'pending',
      description: 'Client inquiring about trademark registration timeline and next steps in the application process.',
      caseNumber: 'CASE-2025-1756',
      assignedTo: 'John Doe',
      lastUpdated: 'October 24, 2025 at 3:45 PM',
      nextSteps: [
        'Check trademark database status',
        'Draft email response',
        'Include timeline estimate',
        'Send supporting documents'
      ],
    },
    {
      id: '4',
      title: 'Schedule Williams consultation',
      client: 'Williams Estate',
      priority: 'medium',
      type: 'call',
      dueDate: 'Tomorrow',
      status: 'pending',
      description: 'Initial consultation for estate planning. Client has multiple properties and complex asset structure.',
      caseNumber: 'CASE-2025-2001',
      assignedTo: 'John Doe',
      lastUpdated: 'October 23, 2025 at 2:20 PM',
      nextSteps: [
        'Coordinate calendars',
        'Send intake questionnaire',
        'Prepare consultation materials',
        'Review asset documentation'
      ],
    },
    {
      id: '5',
      title: 'File Martinez case documents',
      client: 'Martinez Corp',
      priority: 'low',
      type: 'document',
      dueDate: 'This Week',
      status: 'pending',
    },
  ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'call':
        return <PhoneIcon fontSize="small" />;
      case 'email':
        return <EmailIcon fontSize="small" />;
      case 'document':
        return <AssignmentIcon fontSize="small" />;
      case 'review':
        return <CheckCircleIcon fontSize="small" />;
      default:
        return <AssignmentIcon fontSize="small" />;
    }
  };

  const filterTasksByStatus = (status: string) => {
    return tasks.filter((task) => task.status === status);
  };

  const urgentTasks = filterTasksByStatus('urgent');
  const pendingTasks = filterTasksByStatus('pending');
  const completedTasks = filterTasksByStatus('completed');

  const renderTaskCard = (task: Task) => (
    <Card
      key={task.id}
      sx={{
        mb: 2,
        border: task.priority === 'high' ? '2px solid' : '1px solid',
        borderColor: task.priority === 'high' ? 'error.main' : 'divider',
        '&:hover': {
          boxShadow: 3,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s',
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {getTypeIcon(task.type)}
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {task.title}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <PeopleIcon fontSize="inherit" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
              {task.client}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip
                label={task.priority.toUpperCase()}
                size="small"
                color={getPriorityColor(task.priority) as any}
                sx={{ fontWeight: 600 }}
              />
              <Chip
                icon={<ScheduleIcon />}
                label={task.dueDate}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
          <Box>
            {task.priority === 'high' && (
              <FlagIcon color="error" sx={{ mr: 1 }} />
            )}
          </Box>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            size="small"
            endIcon={<ArrowForwardIcon />}
            onClick={() => handleTakeAction(task)}
            sx={{
              bgcolor: '#8a6d4f',
              '&:hover': { bgcolor: '#6d5640' },
            }}
          >
            Take Action
          </Button>
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => handleViewDetails(task)}
          >
            View Details
          </Button>
          <Button variant="outlined" size="small" color="success">
            Complete
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );

  const renderQuickStats = () => {
    // Show loading state
    if (loading && !stats) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      );
    }

    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 3,
          mb: 4,
        }}
      >
        <Card 
          sx={{ 
            bgcolor: '#fff3e0', 
            borderLeft: '4px solid #ff9800',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
          onClick={() => setCurrentTab(0)}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <AssignmentIcon sx={{ color: '#ff9800' }} />
              <Typography variant="h3" sx={{ fontWeight: 700, color: '#ff9800' }}>
                {stats?.total_tasks ?? urgentTasks.length}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Total Tasks
            </Typography>
            {stats && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                {stats.tasks_processing} processing
              </Typography>
            )}
          </CardContent>
        </Card>
        
        <Card 
          sx={{ 
            bgcolor: '#e3f2fd', 
            borderLeft: '4px solid #2196f3',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
          onClick={() => setCurrentTab(1)}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <ScheduleIcon sx={{ color: '#2196f3' }} />
              <Typography variant="h3" sx={{ fontWeight: 700, color: '#2196f3' }}>
                {stats?.tasks_pending ?? pendingTasks.length}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Pending Tasks
            </Typography>
            {stats && stats.tasks_awaiting_approval > 0 && (
              <Typography variant="caption" sx={{ color: '#ff9800', display: 'block', mt: 0.5 }}>
                {stats.tasks_awaiting_approval} awaiting approval
              </Typography>
            )}
          </CardContent>
        </Card>
        
        <Card 
          sx={{ 
            bgcolor: '#e8f5e9', 
            borderLeft: '4px solid #4caf50',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
          onClick={() => setCurrentTab(2)}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CheckCircleIcon sx={{ color: '#4caf50' }} />
              <Typography variant="h3" sx={{ fontWeight: 700, color: '#4caf50' }}>
                {stats?.tasks_completed ?? completedTasks.length}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Completed Tasks
            </Typography>
            {stats && stats.success_rate > 0 && (
              <Typography variant="caption" color="success.main" sx={{ display: 'block', mt: 0.5 }}>
                {stats.success_rate.toFixed(1)}% success rate
              </Typography>
            )}
          </CardContent>
        </Card>
        
        <Card 
          sx={{ 
            bgcolor: '#f3e5f5', 
            borderLeft: '4px solid #9c27b0',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            },
          }}
          onClick={() => navigate('/agents')}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PsychologyIcon sx={{ color: '#9c27b0' }} />
              <Typography variant="h3" sx={{ fontWeight: 700, color: '#9c27b0' }}>
                {stats?.active_agents ?? 0}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Active Agents
            </Typography>
            {stats && stats.cases_scraped_today > 0 && (
              <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                {stats.cases_scraped_today.toLocaleString()} cases today
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          My Work
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {loading && !stats ? (
            'Loading task data...'
          ) : stats ? (
            <>
              {stats.tasks_awaiting_approval > 0 ? (
                <>
                  <strong>{stats.tasks_awaiting_approval}</strong> task{stats.tasks_awaiting_approval > 1 ? 's' : ''} awaiting approval.{' '}
                  {stats.tasks_processing > 0 && `${stats.tasks_processing} more processing.`}
                </>
              ) : stats.tasks_processing > 0 ? (
                <>
                  <strong>{stats.tasks_processing}</strong> task{stats.tasks_processing > 1 ? 's are' : ' is'} being processed by AI agents.
                </>
              ) : (
                `All caught up! ${stats.tasks_completed} tasks completed.`
              )}
            </>
          ) : (
            `Focus on what matters most. ${urgentTasks.length} urgent tasks need your attention.`
          )}
        </Typography>
      </Box>

      {/* Quick Stats */}
      {renderQuickStats()}

      {/* API Error Alert */}
      {error && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          onClose={() => setError(null)}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {error}
          </Typography>
          <Typography variant="caption">
            Showing cached data. The system will retry automatically.
          </Typography>
        </Alert>
      )}

      {/* Intelligent Scraper Performance Card */}
      {stats && stats.cases_scraped_today > 0 && (
        <Card sx={{ mb: 3, bgcolor: '#f5f5f5', border: '2px solid #9c27b0' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <SpeedIcon sx={{ fontSize: 40, color: '#9c27b0' }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#9c27b0' }}>
                  Intelligent Scraper Active
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Real-time legal research across 10.6M opinions
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#9c27b0' }}>
                  {stats.cases_scraped_today.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Cases Scraped Today
                </Typography>
              </Box>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#2196f3' }}>
                  {stats.scraping_speed?.toFixed(1) ?? 'N/A'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Cases/sec (Current)
                </Typography>
              </Box>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#4caf50' }}>
                  {stats.scraping_sessions ?? 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Scraping Sessions
                </Typography>
              </Box>
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#ff9800' }}>
                  {stats.tasks_processing}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Tasks Processing Now
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Urgent Alert */}
      {urgentTasks.length > 0 && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 3,
            cursor: 'pointer',
            '&:hover': {
              bgcolor: 'rgba(211, 47, 47, 0.15)',
            },
            transition: 'background-color 0.2s',
          }}
          onClick={() => setCurrentTab(0)}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {urgentTasks.length} urgent task{urgentTasks.length > 1 ? 's' : ''} require immediate attention - Click to view
          </Typography>
        </Alert>
      )}

      {/* Task Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          sx={{
            '& .MuiTab-root': {
              fontWeight: 600,
              fontSize: '1rem',
            },
          }}
        >
          <Tab
            label={`Urgent Today (${urgentTasks.length})`}
            icon={<FlagIcon />}
            iconPosition="start"
          />
          <Tab
            label={`Pending (${pendingTasks.length})`}
            icon={<ScheduleIcon />}
            iconPosition="start"
          />
          <Tab
            label={`Completed (${completedTasks.length})`}
            icon={<CheckCircleIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Task Lists */}
      <Box>
        {currentTab === 0 && (
          <Box>
            {urgentTasks.length === 0 ? (
              <Alert severity="success">No urgent tasks - great work!</Alert>
            ) : (
              urgentTasks.map(renderTaskCard)
            )}
          </Box>
        )}
        {currentTab === 1 && (
          <Box>
            {pendingTasks.length === 0 ? (
              <Alert severity="info">No pending tasks</Alert>
            ) : (
              pendingTasks.map(renderTaskCard)
            )}
          </Box>
        )}
        {currentTab === 2 && (
          <Box>
            {completedTasks.length === 0 ? (
              <Alert severity="info">No completed tasks today</Alert>
            ) : (
              completedTasks.map(renderTaskCard)
            )}
          </Box>
        )}
      </Box>

      {/* Action Dialog */}
      <Dialog
        open={actionDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Choose Communication Method
          </Typography>
          {selectedTask && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Contact: {selectedTask.client}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          <List sx={{ pt: 0 }}>
            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleActionSelect('email')}
                sx={{
                  borderRadius: 1,
                  mb: 1,
                  border: '2px solid',
                  borderColor: 'divider',
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'primary.50',
                  },
                }}
              >
                <ListItemIcon>
                  <Box
                    sx={{
                      bgcolor: '#1976d2',
                      color: 'white',
                      p: 1.5,
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <EmailIcon />
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary="Send Email"
                  secondary="Compose and send an email message"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItemButton>
            </ListItem>

            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleActionSelect('call')}
                sx={{
                  borderRadius: 1,
                  mb: 1,
                  border: '2px solid',
                  borderColor: 'divider',
                  '&:hover': {
                    borderColor: 'success.main',
                    bgcolor: 'success.50',
                  },
                }}
              >
                <ListItemIcon>
                  <Box
                    sx={{
                      bgcolor: '#2e7d32',
                      color: 'white',
                      p: 1.5,
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <PhoneIcon />
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary="Make Phone Call"
                  secondary="Initiate a voice call"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItemButton>
            </ListItem>

            <ListItem disablePadding>
              <ListItemButton
                onClick={() => handleActionSelect('text')}
                sx={{
                  borderRadius: 1,
                  border: '2px solid',
                  borderColor: 'divider',
                  '&:hover': {
                    borderColor: 'warning.main',
                    bgcolor: 'warning.50',
                  },
                }}
              >
                <ListItemIcon>
                  <Box
                    sx={{
                      bgcolor: '#ed6c02',
                      color: 'white',
                      p: 1.5,
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <SmsIcon />
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary="Send Text Message"
                  secondary="Send an SMS message"
                  primaryTypographyProps={{ fontWeight: 600 }}
                />
              </ListItemButton>
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseDialog} variant="outlined">
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={handleCloseDetailsDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Case Details
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedTask && (
            <Box>
              {/* Header Section */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                  {selectedTask.title}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip
                    label={selectedTask.priority.toUpperCase()}
                    size="small"
                    color={getPriorityColor(selectedTask.priority) as any}
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    icon={getTypeIcon(selectedTask.type)}
                    label={selectedTask.type.toUpperCase()}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={selectedTask.status.toUpperCase()}
                    size="small"
                    color={selectedTask.status === 'urgent' ? 'error' : 'default'}
                    variant="outlined"
                  />
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Case Information Grid */}
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                gap: 3,
                mb: 3 
              }}>
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PeopleIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Client
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {selectedTask.client}
                  </Typography>
                </Box>

                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <FormatListNumberedIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Case Number
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ fontWeight: 500, fontFamily: 'monospace' }}>
                    {selectedTask.caseNumber || 'N/A'}
                  </Typography>
                </Box>

                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PersonIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Assigned To
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {selectedTask.assignedTo || 'Unassigned'}
                  </Typography>
                </Box>

                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <CalendarTodayIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Due Date
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {selectedTask.dueDate}
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Description Section */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600, mb: 1 }}>
                  Description
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                  {selectedTask.description || 'No description available.'}
                </Typography>
              </Box>

              {/* Next Steps Section */}
              {selectedTask.nextSteps && selectedTask.nextSteps.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600, mb: 2 }}>
                      Next Steps
                    </Typography>
                    <List dense sx={{ bgcolor: 'grey.50', borderRadius: 1, p: 1 }}>
                      {selectedTask.nextSteps.map((step, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Box
                              sx={{
                                width: 24,
                                height: 24,
                                borderRadius: '50%',
                                bgcolor: 'primary.main',
                                color: 'white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                              }}
                            >
                              {index + 1}
                            </Box>
                          </ListItemIcon>
                          <ListItemText 
                            primary={step}
                            primaryTypographyProps={{ fontSize: '0.9rem' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </>
              )}

              {/* Last Updated */}
              {selectedTask.lastUpdated && (
                <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">
                    Last updated: {selectedTask.lastUpdated}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={handleCloseDetailsDialog} variant="outlined">
            Close
          </Button>
          <Button 
            variant="contained"
            onClick={() => {
              handleCloseDetailsDialog();
              if (selectedTask) handleTakeAction(selectedTask);
            }}
            sx={{
              bgcolor: '#8a6d4f',
              '&:hover': { bgcolor: '#6d5640' },
            }}
          >
            Take Action
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
