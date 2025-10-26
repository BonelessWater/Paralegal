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
  IconButton,
  Menu,
  MenuItem,
  Alert,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Email as EmailIcon,
  Phone as PhoneIcon,
  Message as MessageIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Flag as FlagIcon,
  Inbox as InboxIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Archive as ArchiveIcon,
  History as HistoryIcon,
  PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import { mockTasks } from '../mockData';

interface Task {
  id: string;
  clientName?: string;
  content: string;
  source?: string;
  priority?: string;
  status?: string;
  aiDraft?: string;
  approvalStatus?: 'new' | 'approved' | 'rejected' | 'archived';
  type?: string;
  timestamp?: string;
  assignedAgent?: string;
  conversationHistory?: Array<{ sender: string; message: string; timestamp: string }>;
}

const InboxView: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSource, setFilterSource] = useState<'all' | 'email' | 'text' | 'call'>('all');
  const [showUrgentOnly, setShowUrgentOnly] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTask, setMenuTask] = useState<Task | null>(null);
  const [tasks, setTasks] = useState<Task[]>(
    mockTasks.map(t => ({ 
      ...t, 
      approvalStatus: 'new' as const,
      conversationHistory: [
        { sender: 'Client', message: t.content, timestamp: t.timestamp || new Date().toISOString() },
        { sender: 'AI Assistant', message: t.aiDraft || 'Draft response pending...', timestamp: new Date().toISOString() }
      ]
    }))
  );
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editedText, setEditedText] = useState('');
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historyTask, setHistoryTask] = useState<Task | null>(null);
  const [reassignDialogOpen, setReassignDialogOpen] = useState(false);
  const [reassignTask, setReassignTask] = useState<Task | null>(null);
  const [selectedAgent, setSelectedAgent] = useState('');

  const handleOpenHistoryDialog = (task: Task) => {
    setHistoryTask(task);
    setHistoryDialogOpen(true);
    setAnchorEl(null);
  };

  const handleCloseHistoryDialog = () => {
    setHistoryDialogOpen(false);
    setHistoryTask(null);
  };

  const handleOpenReassignDialog = (task: Task) => {
    setReassignTask(task);
    setSelectedAgent(task.assignedAgent || '');
    setReassignDialogOpen(true);
    setAnchorEl(null);
  };

  const handleCloseReassignDialog = () => {
    setReassignDialogOpen(false);
    setReassignTask(null);
    setSelectedAgent('');
  };

  const handleReassign = () => {
    if (reassignTask && selectedAgent) {
      setTasks(tasks.map(task => 
        task.id === reassignTask.id 
          ? { ...task, assignedAgent: selectedAgent }
          : task
      ));
      handleCloseReassignDialog();
    }
  };

  const handleArchive = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'archived' as const }
        : task
    ));
    setAnchorEl(null);
  };

  const handleUnarchive = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'new' as const }
        : task
    ));
  };

  const handleOpenEditDialog = (task: Task) => {
    setEditingTask(task);
    setEditedText(task.aiDraft || '');
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setEditingTask(null);
    setEditedText('');
  };

  const handleSaveEdit = () => {
    if (editingTask) {
      setTasks(tasks.map(task => 
        task.id === editingTask.id 
          ? { ...task, aiDraft: editedText }
          : task
      ));
      handleCloseEditDialog();
    }
  };

  const handleApprove = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'approved' as const }
        : task
    ));
  };

  const handleReject = (taskId: string) => {
    setTasks(tasks.map(task => 
      task.id === taskId 
        ? { ...task, approvalStatus: 'rejected' as const }
        : task
    ));
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'email':
        return <EmailIcon />;
      case 'text':
        return <MessageIcon />;
      case 'call':
        return <PhoneIcon />;
      default:
        return <EmailIcon />;
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'email':
        return '#2196f3';
      case 'text':
        return '#4caf50';
      case 'call':
        return '#9c27b0';
      default:
        return '#757575';
    }
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

  const getStatusLabel = (status: string) => {
    return status.replace(/_/g, ' ').toUpperCase();
  };

  const newTasks = tasks.filter(t => t.approvalStatus === 'new');
  const approvedTasks = tasks.filter(t => t.approvalStatus === 'approved');
  const rejectedTasks = tasks.filter(t => t.approvalStatus === 'rejected');
  const archivedTasks = tasks.filter(t => t.approvalStatus === 'archived');

  const getCurrentTabTasks = () => {
    switch (currentTab) {
      case 0: return newTasks;
      case 1: return approvedTasks;
      case 2: return rejectedTasks;
      case 3: return archivedTasks;
      default: return newTasks;
    }
  };

  const filteredTasks = getCurrentTabTasks().filter(task => {
    const matchesSearch = task.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.clientName?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterSource === 'all' || task.source === filterSource;
    const matchesUrgent = !showUrgentOnly || task.priority === 'high';
    return matchesSearch && matchesFilter && matchesUrgent;
  });

  const urgentCount = newTasks.filter(t => t.priority === 'high').length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          New Requests
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {filteredTasks.length} message{filteredTasks.length !== 1 ? 's' : ''} to review
          {currentTab === 0 && urgentCount > 0 && ` • ${urgentCount} urgent`}
        </Typography>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, newValue) => {
            setCurrentTab(newValue);
            setShowUrgentOnly(false); // Clear urgent filter when switching tabs
          }}
          sx={{
            '& .MuiTab-root': {
              fontWeight: 600,
              fontSize: '1rem',
            },
          }}
        >
          <Tab
            label={`New Requests (${newTasks.length})`}
            icon={<InboxIcon />}
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
          <Tab
            label={`Archived (${archivedTasks.length})`}
            icon={<ArchiveIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Urgent Alert */}
      {currentTab === 0 && urgentCount > 0 && (
        <Alert 
          severity="warning" 
          sx={{ 
            mb: 3,
            cursor: showUrgentOnly ? 'default' : 'pointer',
            '&:hover': showUrgentOnly ? {} : { 
              bgcolor: 'rgba(237, 108, 2, 0.1)',
            },
            transition: 'background-color 0.2s',
          }}
          onClick={() => !showUrgentOnly && setShowUrgentOnly(true)}
          action={
            showUrgentOnly && (
              <Button
                size="small"
                startIcon={<CloseIcon />}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowUrgentOnly(false);
                }}
                sx={{ 
                  color: 'warning.main',
                  fontWeight: 600,
                }}
              >
                Show All
              </Button>
            )
          }
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FlagIcon />
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {showUrgentOnly 
                ? `Showing ${urgentCount} high-priority message${urgentCount > 1 ? 's' : ''}`
                : `${urgentCount} high-priority message${urgentCount > 1 ? 's' : ''} need${urgentCount === 1 ? 's' : ''} immediate attention - Click to filter`
              }
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Search and Filter Bar */}
      <Box sx={{ mb: 3 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            fullWidth
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flex: 1 }}
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant={filterSource === 'all' ? 'contained' : 'outlined'}
              onClick={() => setFilterSource('all')}
              sx={{
                bgcolor: filterSource === 'all' ? '#8a6d4f' : 'transparent',
                '&:hover': { bgcolor: filterSource === 'all' ? '#6d5640' : 'rgba(138, 109, 79, 0.1)' },
              }}
            >
              All
            </Button>
            <Button
              variant={filterSource === 'email' ? 'contained' : 'outlined'}
              onClick={() => setFilterSource('email')}
              startIcon={<EmailIcon />}
              sx={{
                bgcolor: filterSource === 'email' ? '#2196f3' : 'transparent',
                borderColor: '#2196f3',
                color: filterSource === 'email' ? '#fff' : '#2196f3',
                '&:hover': { bgcolor: filterSource === 'email' ? '#1976d2' : 'rgba(33, 150, 243, 0.1)' },
              }}
            >
              Email
            </Button>
            <Button
              variant={filterSource === 'text' ? 'contained' : 'outlined'}
              onClick={() => setFilterSource('text')}
              startIcon={<MessageIcon />}
              sx={{
                bgcolor: filterSource === 'text' ? '#4caf50' : 'transparent',
                borderColor: '#4caf50',
                color: filterSource === 'text' ? '#fff' : '#4caf50',
                '&:hover': { bgcolor: filterSource === 'text' ? '#388e3c' : 'rgba(76, 175, 80, 0.1)' },
              }}
            >
              Text
            </Button>
            <Button
              variant={filterSource === 'call' ? 'contained' : 'outlined'}
              onClick={() => setFilterSource('call')}
              startIcon={<PhoneIcon />}
              sx={{
                bgcolor: filterSource === 'call' ? '#9c27b0' : 'transparent',
                borderColor: '#9c27b0',
                color: filterSource === 'call' ? '#fff' : '#9c27b0',
                '&:hover': { bgcolor: filterSource === 'call' ? '#7b1fa2' : 'rgba(156, 39, 176, 0.1)' },
              }}
            >
              Call
            </Button>
          </Stack>
        </Stack>
      </Box>

      {/* Messages List */}
      <Stack spacing={2}>
        {filteredTasks.length === 0 ? (
          <Alert severity="info">No messages found</Alert>
        ) : (
          filteredTasks.map((task) => (
            <Card
              key={task.id}
              sx={{
                border: task.priority === 'high' ? '2px solid' : '1px solid',
                borderColor: task.priority === 'high' ? 'error.main' : 'divider',
                '&:hover': {
                  boxShadow: 4,
                  transform: 'translateY(-2px)',
                  transition: 'all 0.2s',
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  {/* Source Icon */}
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: `${getSourceColor(task.source)}15`,
                      color: getSourceColor(task.source),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {getSourceIcon(task.source)}
                  </Box>

                  {/* Content */}
                  <Box sx={{ flex: 1 }}>
                    {/* Header Row */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          label={getStatusLabel(task.status)}
                          size="small"
                          color={task.status === 'awaiting_approval' ? 'warning' : 'default'}
                          sx={{ fontWeight: 600 }}
                        />
                        {task.priority && (
                          <Chip
                            label={task.priority.toUpperCase()}
                            size="small"
                            color={getPriorityColor(task.priority) as any}
                            icon={task.priority === 'high' ? <FlagIcon /> : undefined}
                          />
                        )}
                        {task.type && (
                          <Chip
                            label={task.type.replace(/_/g, ' ')}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ScheduleIcon fontSize="inherit" />
                          {new Date(task.timestamp).toLocaleString()}
                        </Typography>
                        {/* Hide menu button for archived items */}
                        {currentTab !== 3 && (
                          <IconButton size="small" onClick={(e) => {
                            setAnchorEl(e.currentTarget);
                            setMenuTask(task);
                          }}>
                            <MoreVertIcon />
                          </IconButton>
                        )}
                      </Box>
                    </Box>

                    {/* Client Name */}
                    {task.clientName && (
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <PersonIcon fontSize="small" />
                        {task.clientName}
                      </Typography>
                    )}

                    {/* Message Content */}
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {task.content}
                    </Typography>

                    {/* AI Draft Preview */}
                    {task.aiDraft && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1, borderLeft: '3px solid #8a6d4f' }}>
                        <Typography variant="caption" sx={{ fontWeight: 600, color: '#8a6d4f', mb: 1, display: 'block' }}>
                          AI DRAFT READY FOR REVIEW
                        </Typography>
                        <Typography variant="body2" sx={{ fontSize: '0.875rem', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                          {task.aiDraft.length > 200 ? task.aiDraft.substring(0, 200) + '...' : task.aiDraft}
                        </Typography>
                      </Box>
                    )}

                    {/* Assigned Agent */}
                    {task.assignedAgent && (
                      <Box sx={{ mt: 2 }}>
                        <Chip
                          label={`Assigned to: ${task.assignedAgent.replace(/_/g, ' ')}`}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </Box>
                    )}

                    <Divider sx={{ my: 2 }} />

                    {/* Action Buttons */}
                    <Stack direction="row" spacing={1}>
                      {currentTab === 0 && task.status === 'awaiting_approval' ? (
                        <>
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<CheckCircleIcon />}
                            onClick={() => handleApprove(task.id)}
                            sx={{
                              bgcolor: '#059669',
                              '&:hover': { bgcolor: '#047857' },
                            }}
                          >
                            Approve & Send
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => handleOpenEditDialog(task)}
                          >
                            Edit Draft
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small" 
                            color="error"
                            startIcon={<CancelIcon />}
                            onClick={() => handleReject(task.id)}
                          >
                            Reject
                          </Button>
                        </>
                      ) : currentTab === 0 ? (
                        <>
                          <Button
                            variant="contained"
                            size="small"
                            sx={{
                              bgcolor: '#8a6d4f',
                              '&:hover': { bgcolor: '#6d5640' },
                            }}
                          >
                            Take Action
                          </Button>
                          <Button variant="outlined" size="small">
                            View Details
                          </Button>
                          <Button 
                            variant="outlined" 
                            size="small" 
                            color="success"
                            onClick={() => handleApprove(task.id)}
                          >
                            Mark Complete
                          </Button>
                        </>
                      ) : currentTab === 1 ? (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            setTasks(tasks.map(t => 
                              t.id === task.id 
                                ? { ...t, approvalStatus: 'new' as const }
                                : t
                            ));
                            setCurrentTab(0);
                          }}
                        >
                          Move Back to New
                        </Button>
                      ) : currentTab === 2 ? (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            setTasks(tasks.map(t => 
                              t.id === task.id 
                                ? { ...t, approvalStatus: 'new' as const }
                                : t
                            ));
                            setCurrentTab(0);
                          }}
                        >
                          Move Back to New
                        </Button>
                      ) : currentTab === 3 ? (
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<InboxIcon />}
                          onClick={() => handleUnarchive(task.id)}
                          sx={{
                            bgcolor: '#8a6d4f',
                            '&:hover': { bgcolor: '#6d5640' },
                          }}
                        >
                          Unarchive
                        </Button>
                      ) : null}
                    </Stack>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))
        )}
      </Stack>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => {
          setAnchorEl(null);
          setMenuTask(null);
        }}
      >
        <MenuItem 
          onClick={() => menuTask && handleOpenHistoryDialog(menuTask)}
          sx={{ display: 'flex', gap: 1 }}
        >
          <HistoryIcon fontSize="small" />
          View Full History
        </MenuItem>
        <MenuItem 
          onClick={() => menuTask && handleOpenReassignDialog(menuTask)}
          sx={{ display: 'flex', gap: 1 }}
        >
          <PersonAddIcon fontSize="small" />
          Reassign
        </MenuItem>
        <MenuItem 
          onClick={() => menuTask && handleArchive(menuTask.id)}
          sx={{ display: 'flex', gap: 1 }}
        >
          <ArchiveIcon fontSize="small" />
          Archive
        </MenuItem>
        <Divider />
        <MenuItem 
          onClick={() => {
            setAnchorEl(null);
            setMenuTask(null);
          }} 
          sx={{ color: 'error.main', display: 'flex', gap: 1 }}
        >
          <CancelIcon fontSize="small" />
          Delete
        </MenuItem>
      </Menu>

      {/* Edit Draft Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={handleCloseEditDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EditIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Edit Draft Message
            </Typography>
          </Box>
          {editingTask && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              For: {editingTask.clientName || 'Client'}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'text.secondary' }}>
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
                {editingTask?.content}
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
              AI Draft (Editable):
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={12}
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              variant="outlined"
              placeholder="Edit your message here..."
              sx={{
                '& .MuiOutlinedInput-root': {
                  fontFamily: 'inherit',
                  fontSize: '0.95rem',
                  lineHeight: 1.6,
                },
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {editedText.length} characters
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button 
            onClick={handleCloseEditDialog} 
            variant="outlined"
            startIcon={<CloseIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveEdit}
            variant="contained"
            startIcon={<SaveIcon />}
            sx={{
              bgcolor: '#059669',
              '&:hover': { bgcolor: '#047857' },
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Full History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={handleCloseHistoryDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Conversation History
            </Typography>
          </Box>
          {historyTask && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Client: {historyTask.clientName || 'Unknown'} • {historyTask.content.substring(0, 60)}...
            </Typography>
          )}
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {historyTask?.conversationHistory?.map((entry, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: entry.sender === 'Client' ? '#f5f5f5' : '#e8f4f8',
                  border: '1px solid',
                  borderColor: entry.sender === 'Client' ? 'divider' : 'primary.light',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: entry.sender === 'Client' ? 'text.primary' : 'primary.main' }}>
                    {entry.sender}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(entry.timestamp).toLocaleString()}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {entry.message}
                </Typography>
              </Box>
            ))}
            {(!historyTask?.conversationHistory || historyTask.conversationHistory.length === 0) && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No conversation history available
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button 
            onClick={handleCloseHistoryDialog} 
            variant="contained"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reassign Dialog */}
      <Dialog
        open={reassignDialogOpen}
        onClose={handleCloseReassignDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonAddIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Reassign Case
            </Typography>
          </Box>
          {reassignTask && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {reassignTask.content.substring(0, 60)}...
            </Typography>
          )}
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Current Agent:
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {reassignTask?.assignedAgent || 'Unassigned'}
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Reassign To:
            </Typography>
            <TextField
              select
              fullWidth
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              variant="outlined"
            >
              <MenuItem value="communicator">Communicator Agent</MenuItem>
              <MenuItem value="email_agent">Email Specialist</MenuItem>
              <MenuItem value="sms_agent">SMS Agent</MenuItem>
              <MenuItem value="voice_agent">Voice Call Agent</MenuItem>
              <MenuItem value="legal_research">Legal Research AI</MenuItem>
              <MenuItem value="document_prep">Document Preparation</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button 
            onClick={handleCloseReassignDialog} 
            variant="outlined"
            startIcon={<CloseIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleReassign}
            variant="contained"
            startIcon={<PersonAddIcon />}
            disabled={!selectedAgent || selectedAgent === reassignTask?.assignedAgent}
            sx={{
              bgcolor: '#059669',
              '&:hover': { bgcolor: '#047857' },
            }}
          >
            Reassign
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InboxView;
