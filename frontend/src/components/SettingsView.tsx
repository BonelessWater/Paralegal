import React, { useState } from 'react';
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
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  SmartToy as SmartToyIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
} from '@mui/icons-material';

const SettingsView: React.FC = () => {
  const [autoApprove, setAutoApprove] = useState(false);
  const [aiConfidence, setAiConfidence] = useState(75);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          AI Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure AI agents and system preferences
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
        {/* AI Agent Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SmartToyIcon />
              AI Agent Configuration
            </Typography>

            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Auto-Approval Threshold
                </Typography>
                <Box sx={{ px: 1 }}>
                  <Slider
                    value={aiConfidence}
                    onChange={(_, value) => setAiConfidence(value as number)}
                    valueLabelDisplay="on"
                    min={50}
                    max={100}
                    marks={[
                      { value: 50, label: '50%' },
                      { value: 75, label: '75%' },
                      { value: 100, label: '100%' },
                    ]}
                    sx={{
                      '& .MuiSlider-thumb': {
                        bgcolor: '#8a6d4f',
                      },
                      '& .MuiSlider-track': {
                        bgcolor: '#8a6d4f',
                      },
                    }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  AI responses with confidence above {aiConfidence}% will be auto-approved
                </Typography>
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={autoApprove}
                    onChange={(e) => setAutoApprove(e.target.checked)}
                  />
                }
                label="Enable Auto-Approval"
              />

              <Divider />

              <FormControl fullWidth>
                <InputLabel>Response Tone</InputLabel>
                <Select defaultValue="professional" label="Response Tone">
                  <MenuItem value="professional">Professional</MenuItem>
                  <MenuItem value="empathetic">Empathetic</MenuItem>
                  <MenuItem value="formal">Formal</MenuItem>
                  <MenuItem value="friendly">Friendly</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Default Language</InputLabel>
                <Select defaultValue="english" label="Default Language">
                  <MenuItem value="english">English</MenuItem>
                  <MenuItem value="spanish">Spanish</MenuItem>
                  <MenuItem value="french">French</MenuItem>
                </Select>
              </FormControl>

              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                sx={{
                  bgcolor: '#8a6d4f',
                  '&:hover': { bgcolor: '#6d5640' },
                }}
              >
                Save AI Settings
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Communication Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <EmailIcon />
              Communication Channels
            </Typography>

            <Stack spacing={2}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Email Integration"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="SMS Integration (Twilio)"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Voice Calls (ElevenLabs)"
              />
              <FormControlLabel
                control={<Switch />}
                label="WhatsApp Integration"
              />

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                SendGrid API Key
              </Typography>
              <TextField
                fullWidth
                type="password"
                placeholder="••••••••••••••••"
                variant="outlined"
                size="small"
              />

              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Twilio Account SID
              </Typography>
              <TextField
                fullWidth
                type="password"
                placeholder="••••••••••••••••"
                variant="outlined"
                size="small"
              />

              <Button variant="outlined" startIcon={<RefreshIcon />}>
                Test Connections
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Performance Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SpeedIcon />
              Performance & Processing
            </Typography>

            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Current Backend
                </Typography>
                <Stack direction="row" spacing={1}>
                  <Chip
                    label="vLLM Enabled"
                    color="success"
                    size="small"
                  />
                  <Chip
                    label="AMD MI300X"
                    color="primary"
                    size="small"
                  />
                </Stack>
              </Box>

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Processing Speed
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#4caf50' }}>
                  320 tokens/sec
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  71% faster than baseline
                </Typography>
              </Box>

              <Divider />

              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable GPU acceleration"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Batch processing"
              />
              <FormControlLabel
                control={<Switch />}
                label="Priority queue for high-priority tasks"
              />
            </Stack>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon />
              Security & Privacy
            </Typography>

            <Stack spacing={2}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Require approval for all AI responses"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable audit logging"
              />
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Encrypt client data at rest"
              />
              <FormControlLabel
                control={<Switch />}
                label="Two-factor authentication required"
              />

              <Divider sx={{ my: 2 }} />

              <Button variant="outlined" fullWidth>
                View Audit Logs
              </Button>
              <Button variant="outlined" fullWidth>
                Export Security Report
              </Button>
              <Button variant="outlined" fullWidth color="error">
                Reset All Settings
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default SettingsView;
