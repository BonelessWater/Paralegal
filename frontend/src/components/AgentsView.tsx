import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  TrendingUp as ActivityIcon,
  Schedule as ClockIcon,
  CheckCircle as CheckCircle2Icon,
} from '@mui/icons-material';
import { mockAgents } from '../mockData';

const AgentsView: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e', mb: 1 }}>
          Team Status
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Specialist agents powered by AMD MI300X + Google ADK
        </Typography>
      </Box>

      {/* Agent Cards Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
          gap: 3,
          mb: 4,
        }}
      >
        {mockAgents.map((agent) => (
          <Card
            key={agent.id}
            sx={{
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s',
              },
            }}
          >
            <CardContent>
              {/* Icon and Title */}
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                <Box sx={{ fontSize: '3rem', mb: 2 }}>
                  {agent.icon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                  {agent.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {agent.description}
                </Typography>
              </Box>

              {/* Stats */}
              <Box sx={{ borderTop: '1px solid', borderColor: 'divider', pt: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ActivityIcon sx={{ fontSize: '1rem', color: '#2196f3' }} />
                    <Typography variant="body2" color="text.secondary">
                      Active Tasks
                    </Typography>
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#2196f3' }}>
                    {agent.activeTasksCount}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircle2Icon sx={{ fontSize: '1rem', color: '#4caf50' }} />
                    <Typography variant="body2" color="text.secondary">
                      Completed Today
                    </Typography>
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#4caf50' }}>
                    {agent.completedToday}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ClockIcon sx={{ fontSize: '1rem', color: '#9c27b0' }} />
                    <Typography variant="body2" color="text.secondary">
                      Avg Processing
                    </Typography>
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#9c27b0' }}>
                    {agent.avgProcessingTime}s
                  </Typography>
                </Box>
              </Box>

              {/* Performance Bar */}
              <Box
                sx={{
                  bgcolor: '#f5f5f5',
                  borderRadius: 2,
                  p: 2,
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Performance
                  </Typography>
                  <Chip
                    label="Excellent"
                    size="small"
                    color="success"
                    sx={{ height: 20, fontSize: '0.7rem', fontWeight: 600 }}
                  />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={92}
                  sx={{
                    height: 8,
                    borderRadius: 1,
                    bgcolor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: '#4caf50',
                      borderRadius: 1,
                    },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Architecture Info Card */}
      <Card
        sx={{
          background: 'linear-gradient(135deg, #3a434e 0%, #1a1f24 100%)',
          color: 'white',
        }}
      >
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
            Agent Architecture
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
              gap: 3,
            }}
          >
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.7, mb: 1 }}>
                Orchestration
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#4285f4' }}>
                Google Agent Development Kit (ADK)
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.6 }}>
                Agent-to-Agent (A2A) Protocol
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.7, mb: 1 }}>
                Compute
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#ed1c24' }}>
                AMD MI300X 192GB
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.6 }}>
                ROCm + vLLM Inference Server
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" sx={{ opacity: 0.7, mb: 1 }}>
                Model
              </Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Llama 3 70B
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.6 }}>
                320 tokens/sec throughput
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AgentsView;
