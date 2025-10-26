import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Stack,
  Divider,
  TextField,
  Alert,
  IconButton,
  Tooltip,
  Badge,
  Tabs,
  Tab,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  Send as SendIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Flag as FlagIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import { mockTasks } from '../mockData';

interface Task {
  id: string;
  client: string;
  originalMessage: string;
  aiDraft?: string;
  priority?: string;
  dueDate?: string;
  source?: string;
  status?: string;
  approvalStatus?: 'pending' | 'approved' | 'rejected';
}

const ApprovalQueue: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [editingTask, setEditingTask] = useState<string | null>(null);
  const [editedText, setEditedText] = useState('');
  const [tasks, setTasks] = useState<Task[]>(
    mockTasks
      .filter(t => t.status === 'awaiting_approval')
      .map(t => ({ ...t, approvalStatus: 'pending' as const }))
  );

  const pendingTasks = tasks.filter(t => t.approvalStatus === 'pending');
  const approvedTasks = tasks.filter(t => t.approvalStatus === 'approved');
  const rejectedTasks = tasks.filter(t => t.approvalStatus === 'rejected');

  const handleApprove = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'approved' as const }
        : task
    ));
    setEditingTask(null);
    // Here you would integrate with backend to send the message
    console.log('Approved and sent task:', taskId);
  };

  const handleReject = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'rejected' as const }
        : task
    ));
    setEditingTask(null);
    console.log('Rejected task:', taskId);
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task.id);
    setEditedText(task.aiDraft || '');
  };

  const handleSaveEdit = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, aiDraft: editedText }
        : task
    ));
    setEditingTask(null);
    console.log('Saved edits for task:', taskId);
  };

  const handleCancelEdit = () => {
    setEditingTask(null);
    setEditedText('');
  };

  const getPriorityColor = (priority?: string) => {
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

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          Review Queue
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Review AI-generated responses before sending
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, newValue) => setCurrentTab(newValue)}
          sx={{
            '& .MuiTab-root': {
              fontWeight: 600,
              fontSize: '1rem',
            },
          }}
        >
          <Tab
            label={`Pending Review (${pendingTasks.length})`}
            icon={<PendingIcon />}
            iconPosition="start"
          />
          <Tab
            label={`Approved (${approvedTasks.length})`}
            icon={<ThumbUpIcon />}
            iconPosition="start"
          />
          <Tab
            label={`Rejected (${rejectedTasks.length})`}
            icon={<ThumbDownIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tasks List */}
      {currentTab === 0 && (
        <Stack spacing={3}>
          {pendingTasks.length === 0 ? (
            <Card sx={{ bgcolor: '#e8f5e9', border: '2px solid #4caf50' }}>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <CheckCircleIcon sx={{ fontSize: 64, color: '#4caf50', mb: 2 }} />
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#2e7d32', mb: 1 }}>
                  All Caught Up!
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  No tasks awaiting approval right now.
                </Typography>
              </CardContent>
            </Card>
          ) : (
            pendingTasks.map((task) => (
              <Card
                key={task.id}
                sx={{
                  border: task.priority === 'high' ? '2px solid' : '1px solid',
                  borderColor: task.priority === 'high' ? 'error.main' : 'divider',
                  boxShadow: 3,
                }}
              >
              <CardContent>
                {/* Header Section */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Chip
                      label="AWAITING APPROVAL"
                      color="warning"
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                    {task.type && (
                      <Chip
                        label={task.type.replace(/_/g, ' ').toUpperCase()}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    )}
                    {task.priority && (
                      <Chip
                        label={task.priority.toUpperCase()}
                        size="small"
                        color={getPriorityColor(task.priority) as any}
                        icon={task.priority === 'high' ? <FlagIcon /> : undefined}
                      />
                    )}
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ScheduleIcon fontSize="inherit" />
                    {new Date(task.timestamp).toLocaleString()}
                  </Typography>
                </Box>

                {/* Client Name */}
                {task.clientName && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <PersonIcon fontSize="small" />
                      Client: {task.clientName}
                    </Typography>
                  </Box>
                )}

                {/* Original Message */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: '#3a434e' }}>
                    Original Message:
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: '#f5f5f5',
                      border: '1px solid #e0e0e0',
                      borderRadius: 1,
                      p: 2,
                    }}
                  >
                    <Typography variant="body2" sx={{ color: 'text.secondary', lineHeight: 1.6 }}>
                      {task.content}
                    </Typography>
                  </Box>
                </Box>

                {/* AI-Generated Response */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#3a434e' }}>
                      AI-Generated Response:
                      {task.assignedAgent && (
                        <Typography component="span" variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
                          (by {task.assignedAgent.replace(/_/g, ' ')})
                        </Typography>
                      )}
                    </Typography>
                    {!editingTask && (
                      <Tooltip title="Edit response">
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(task)}
                          sx={{ color: '#8a6d4f' }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  {editingTask === task.id ? (
                    <Box>
                      <TextField
                        fullWidth
                        multiline
                        rows={10}
                        value={editedText}
                        onChange={(e) => setEditedText(e.target.value)}
                        variant="outlined"
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            fontFamily: 'monospace',
                            fontSize: '0.875rem',
                          },
                        }}
                      />
                      <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<SaveIcon />}
                          onClick={() => handleSaveEdit(task.id)}
                          sx={{
                            bgcolor: '#059669',
                            '&:hover': { bgcolor: '#047857' },
                          }}
                        >
                          Save Changes
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<CloseIcon />}
                          onClick={handleCancelEdit}
                        >
                          Cancel
                        </Button>
                      </Stack>
                    </Box>
                  ) : (
                    <Box
                      sx={{
                        bgcolor: '#e3f2fd',
                        border: '2px solid #2196f3',
                        borderRadius: 1,
                        p: 2,
                        position: 'relative',
                      }}
                    >
                      <Typography
                        variant="body2"
                        component="pre"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'inherit',
                          color: 'text.primary',
                          lineHeight: 1.6,
                          m: 0,
                        }}
                      >
                        {task.aiDraft}
                      </Typography>
                    </Box>
                  )}
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* Footer Actions */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <SendIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      Will be sent via: <strong>{task.outreachType || 'email'}</strong>
                    </Typography>
                  </Stack>
                  <Stack direction="row" spacing={1}>
                    <Button
                      variant="outlined"
                      color="error"
                      size="medium"
                      startIcon={<CancelIcon />}
                      onClick={() => handleReject(task.id)}
                    >
                      Reject
                    </Button>
                    <Button
                      variant="contained"
                      size="medium"
                      startIcon={<CheckCircleIcon />}
                      onClick={() => handleApprove(task.id)}
                      sx={{
                        bgcolor: '#059669',
                        '&:hover': { bgcolor: '#047857' },
                      }}
                    >
                      Approve & Send
                    </Button>
                  </Stack>
                </Box>
              </CardContent>
            </Card>
          ))
        )}
      </Stack>
      )}

      {/* Approved Tab */}
      {currentTab === 1 && (
        <Stack spacing={3}>
          {approvedTasks.length === 0 ? (
            <Alert severity="info">No approved messages yet</Alert>
          ) : (
            approvedTasks.map((task) => (
              <Card
                key={task.id}
                sx={{
                  border: '2px solid #4caf50',
                  bgcolor: '#f1f8f4',
                  boxShadow: 2,
                }}
              >
                <CardContent>
                  {/* Header Info */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <EmailIcon fontSize="small" color="action" />
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {task.source === 'email' ? 'Email' : task.source === 'sms' ? 'SMS' : 'Call'} Response
                        </Typography>
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="APPROVED & SENT"
                          size="small"
                          color="success"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PersonIcon fontSize="small" />
                        <Typography variant="body2" color="text.secondary">
                          {task.client}
                        </Typography>
                        {task.priority && (
                          <Chip
                            label={task.priority.toUpperCase()}
                            size="small"
                            color={getPriorityColor(task.priority) as any}
                          />
                        )}
                      </Box>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Sent Message */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'success.dark' }}>
                      Message Sent:
                    </Typography>
                    <Box
                      sx={{
                        bgcolor: 'white',
                        p: 2,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'success.light',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {task.aiDraft}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </Stack>
      )}

      {/* Rejected Tab */}
      {currentTab === 2 && (
        <Stack spacing={3}>
          {rejectedTasks.length === 0 ? (
            <Alert severity="info">No rejected messages</Alert>
          ) : (
            rejectedTasks.map((task) => (
              <Card
                key={task.id}
                sx={{
                  border: '2px solid #f44336',
                  bgcolor: '#fef2f2',
                  boxShadow: 2,
                }}
              >
                <CardContent>
                  {/* Header Info */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <EmailIcon fontSize="small" color="action" />
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {task.source === 'email' ? 'Email' : task.source === 'sms' ? 'SMS' : 'Call'} Response
                        </Typography>
                        <Chip
                          icon={<CancelIcon />}
                          label="REJECTED"
                          size="small"
                          color="error"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PersonIcon fontSize="small" />
                        <Typography variant="body2" color="text.secondary">
                          {task.client}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Original Message */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                      Original Message:
                    </Typography>
                    <Box
                      sx={{
                        bgcolor: '#f5f5f5',
                        p: 2,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography variant="body2" color="text.secondary">
                        {task.originalMessage}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Rejected Draft */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'error.dark' }}>
                      Rejected Draft:
                    </Typography>
                    <Box
                      sx={{
                        bgcolor: 'white',
                        p: 2,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'error.light',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {task.aiDraft}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Action to Re-review */}
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setTasks(tasks.map(t => 
                          t.id === task.id 
                            ? { ...t, approvalStatus: 'pending' as const }
                            : t
                        ));
                        setCurrentTab(0);
                      }}
                    >
                      Move Back to Pending
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </Stack>
      )}
    </Box>
  );
};

export default ApprovalQueue;
