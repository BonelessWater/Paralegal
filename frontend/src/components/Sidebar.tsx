import { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
  Chip,
  useTheme,
  useMediaQuery,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
} from '@mui/material';
import {
  Home as HomeIcon,
  Inbox as InboxIcon,
  CheckCircle as CheckCircleIcon,
  People as PeopleIcon,
  Send as SendIcon,
  Description as DescriptionIcon,
  Schedule as ScheduleIcon,
  Memory as MemoryIcon,
  Cloud as CloudIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { Link, useLocation, useNavigate } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { 
    path: '/', 
    icon: HomeIcon, 
    label: 'My Work', 
    description: 'Today\'s tasks & priorities', 
    badge: 0 
  },
  { 
    path: '/inbox', 
    icon: InboxIcon, 
    label: 'Inbox', 
    description: 'New client messages', 
    badge: 8 
  },
  { 
    path: '/approval', 
    icon: CheckCircleIcon, 
    label: 'Review Drafts', 
    description: 'AI drafts to approve', 
    badge: 3 
  },
  { 
    path: '/history', 
    icon: DescriptionIcon, 
    label: 'History', 
    description: 'Sent & archived' 
  },
];

const drawerWidth = 280;

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [documentTitle, setDocumentTitle] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [callDateTime, setCallDateTime] = useState('');
  const [callParticipant, setCallParticipant] = useState('');

  const handleNewDocument = () => {
    setDocumentDialogOpen(true);
  };

  const handleScheduleCall = () => {
    setScheduleDialogOpen(true);
  };

  const handleCreateDocument = () => {
    // Navigate to document editor with title and type
    const encodedTitle = encodeURIComponent(documentTitle);
    const encodedType = encodeURIComponent(documentType);
    navigate(`/document/${encodedTitle}/${encodedType}`);
    setDocumentDialogOpen(false);
    setDocumentTitle('');
    setDocumentType('');
  };

  const handleScheduleCallSubmit = () => {
    // Here you would integrate with your backend to schedule the call
    console.log('Scheduling call:', { dateTime: callDateTime, participant: callParticipant });
    alert(`Call scheduled with ${callParticipant} for ${new Date(callDateTime).toLocaleString()}`);
    setScheduleDialogOpen(false);
    setCallDateTime('');
    setCallParticipant('');
  };

  const drawerContent = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'secondary.main',
        color: 'white',
      }}
    >
      {/* Logo Section */}
      <Box
        sx={{
          p: 3,
          borderBottom: '1px solid',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          background: 'linear-gradient(135deg, rgba(138, 109, 79, 0.1) 0%, transparent 100%)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box
            component="img"
            src="/lawgorithm.png"
            alt="Lawgorithm Logo"
            sx={{
              width: 48,
              height: 48,
              borderRadius: 1.5,
              mr: 1.5,
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
              objectFit: 'contain',
              bgcolor: 'white',
              p: 0.5,
            }}
          />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.125rem', lineHeight: 1.2 }}>
              Lawgorithm
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.75rem' }}>
              Paralegal Assistant
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation */}
      <List sx={{ flex: 1, px: 2, py: 2 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={Link}
                to={item.path}
                selected={isActive}
                onClick={isMobile ? onClose : undefined}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  px: 2,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(138, 109, 79, 0.2)',
                    borderLeft: '4px solid',
                    borderColor: 'primary.main',
                    '&:hover': {
                      bgcolor: 'rgba(138, 109, 79, 0.25)',
                    },
                  },
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.08)',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: isActive ? 'primary.light' : 'rgba(255, 255, 255, 0.7)' }}>
                  <Icon />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography variant="body2" sx={{ fontWeight: isActive ? 600 : 500, fontSize: '0.9375rem' }}>
                        {item.label}
                      </Typography>
                      {item.badge && (
                        <Chip
                          label={item.badge}
                          size="small"
                          sx={{
                            height: 20,
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            bgcolor: 'error.main',
                            color: 'white',
                            ml: 1,
                          }}
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '0.75rem' }}>
                      {item.description}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

      {/* Quick Actions */}
      <Box sx={{ px: 2, py: 2 }}>
        <Typography
          variant="caption"
          sx={{
            color: 'primary.light',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            fontSize: '0.75rem',
            mb: 1,
            display: 'block',
          }}
        >
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <ListItemButton
            onClick={handleNewDocument}
            sx={{
              borderRadius: 1.5,
              py: 1,
              px: 1.5,
              '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.08)' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: 'rgba(255, 255, 255, 0.7)' }}>
              <DescriptionIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="New Document"
              primaryTypographyProps={{ variant: 'body2', fontSize: '0.875rem' }}
            />
          </ListItemButton>
          <ListItemButton
            onClick={handleScheduleCall}
            sx={{
              borderRadius: 1.5,
              py: 1,
              px: 1.5,
              '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.08)' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: 'rgba(255, 255, 255, 0.7)' }}>
              <ScheduleIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Schedule Call"
              primaryTypographyProps={{ variant: 'body2', fontSize: '0.875rem' }}
            />
          </ListItemButton>
        </Box>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />

      {/* System Status */}
      <Box
        sx={{
          p: 2,
          background: 'linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.2) 100%)',
        }}
      >
        <Box
          sx={{
            bgcolor: 'rgba(0, 0, 0, 0.2)',
            borderRadius: 2,
            p: 2,
            border: '1px solid',
            borderColor: 'rgba(138, 109, 79, 0.3)',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: 'primary.light',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontSize: '0.7rem',
              mb: 1.5,
              display: 'block',
            }}
          >
            System Status
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MemoryIcon sx={{ fontSize: '1rem', color: '#ef4444' }} />
                <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.8125rem' }}>
                  AMD MI300X
                </Typography>
              </Box>
              <Box
                className="status-dot active"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: '#10b981',
                  boxShadow: '0 0 8px rgba(16, 185, 129, 0.8)',
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CloudIcon sx={{ fontSize: '1rem', color: '#3b82f6' }} />
                <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.8125rem' }}>
                  Google ADK
                </Typography>
              </Box>
              <Box
                className="status-dot active"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: '#10b981',
                  boxShadow: '0 0 8px rgba(16, 185, 129, 0.8)',
                }}
              />
            </Box>
          </Box>
          <Divider sx={{ my: 1.5, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="caption"
              sx={{
                color: 'primary.light',
                fontWeight: 700,
                fontSize: '0.75rem',
                display: 'block',
                mb: 0.5,
              }}
            >
              vLLM + ROCm
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.5)', fontSize: '0.7rem' }}>
              All systems operational
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile Drawer */}
      {isMobile ? (
        <Drawer
          variant="temporary"
          open={isOpen}
          onClose={onClose}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              border: 'none',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        /* Desktop Drawer */
        <Drawer
          variant="permanent"
          sx={{
            width: isOpen ? drawerWidth : 0,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              border: 'none',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
          open={isOpen}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* New Document Dialog */}
      <Dialog
        open={documentDialogOpen}
        onClose={() => setDocumentDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DescriptionIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Create New Document
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Document Title"
              fullWidth
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
              placeholder="Enter document title..."
              variant="outlined"
            />
            <TextField
              label="Document Type"
              fullWidth
              select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              SelectProps={{ native: true }}
              variant="outlined"
            >
              <option value="">-- Select type --</option>
              <option value="demand_letter">Demand Letter</option>
              <option value="settlement_agreement">Settlement Agreement</option>
              <option value="complaint">Complaint</option>
              <option value="motion">Motion</option>
              <option value="medical_records_request">Medical Records Request</option>
              <option value="memo">Legal Memo</option>
              <option value="contract">Contract</option>
              <option value="other">Other</option>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={() => {
              setDocumentDialogOpen(false);
              setDocumentTitle('');
              setDocumentType('');
            }}
            variant="outlined"
            startIcon={<CloseIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreateDocument}
            variant="contained"
            disabled={!documentTitle || !documentType}
            sx={{
              bgcolor: '#8a6d4f',
              '&:hover': { bgcolor: '#6d5640' },
            }}
          >
            Create Document
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Call Dialog */}
      <Dialog
        open={scheduleDialogOpen}
        onClose={() => setScheduleDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Schedule Call
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <TextField
              label="Participant Name/Client"
              fullWidth
              value={callParticipant}
              onChange={(e) => setCallParticipant(e.target.value)}
              placeholder="Enter name or client..."
              variant="outlined"
              autoFocus
            />
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, color: 'text.secondary' }}>
                Date & Time
              </Typography>
              <TextField
                type="datetime-local"
                fullWidth
                value={callDateTime}
                onChange={(e) => setCallDateTime(e.target.value)}
                variant="outlined"
                InputLabelProps={{ shrink: true }}
                inputProps={{
                  min: new Date().toISOString().slice(0, 16),
                }}
                sx={{
                  '& input[type="datetime-local"]': {
                    fontSize: '1rem',
                    padding: '16.5px 14px',
                  },
                }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={() => {
              setScheduleDialogOpen(false);
              setCallDateTime('');
              setCallParticipant('');
            }}
            variant="outlined"
            startIcon={<CloseIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleScheduleCallSubmit}
            variant="contained"
            disabled={!callParticipant || !callDateTime}
            sx={{
              bgcolor: '#8a6d4f',
              '&:hover': { bgcolor: '#6d5640' },
            }}
          >
            Schedule Call
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
