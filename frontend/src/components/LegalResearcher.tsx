import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Divider,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  Gavel as GavelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Description as DescriptionIcon,
  Link as LinkIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { ingestTask, getTask, approveTask, type Task } from '../services/api';

interface CaseData {
  case_name: string;
  citation: string;
  court: string;
  date_filed: string;
  snippet: string;
  url: string;
}

const LegalResearcher: React.FC = () => {
  // Form state
  const [question, setQuestion] = useState('');
  const [priority, setPriority] = useState<'high' | 'medium' | 'low'>('high');
  
  // Research state
  const [isResearching, setIsResearching] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [researchProgress, setResearchProgress] = useState<{
    stage: 'idle' | 'pending' | 'processing' | 'awaiting_approval' | 'completed' | 'failed';
    message: string;
    synthesisStage?: number; // 1-4 for multi-stage synthesis tracking
  }>({ stage: 'idle', message: '' });
  const [researchStartTime, setResearchStartTime] = useState<number | null>(null);
  
  // Results state
  const [cases, setCases] = useState<CaseData[]>([]);
  const [researchMemo, setResearchMemo] = useState('');
  const [selectedCase, setSelectedCase] = useState<CaseData | null>(null);
  const [caseDialogOpen, setCaseDialogOpen] = useState(false);
  
  // Sample questions
  const sampleQuestions = [
    "Research premises liability cases involving slip and fall with inadequate warning signs",
    "Medical malpractice cases with misdiagnosis of heart conditions leading to patient death",
    "Employment discrimination wrongful termination cases with whistleblower claims",
    "Product liability cases involving defective medical devices",
  ];

  // Poll task status and estimate synthesis stage
  useEffect(() => {
    if (!currentTask?.id || currentTask.status === 'approved' || currentTask.status === 'failed') {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const updatedTask = await getTask(currentTask.id);
        setCurrentTask(updatedTask);
        
        // Estimate synthesis stage based on processing time and status
        let synthesisStage: number | undefined;
        if (updatedTask.status === 'processing' && researchStartTime) {
          const elapsedSeconds = (Date.now() - researchStartTime) / 1000;
          
          // Typical timing: 0-15s = scraping, 15-30s = Stage 1&2, 30-60s = Stage 3, 60-90s = Stage 4
          if (elapsedSeconds < 15) {
            synthesisStage = undefined; // Still scraping
          } else if (elapsedSeconds < 30) {
            synthesisStage = 1; // Stage 1: Organizing findings
          } else if (elapsedSeconds < 45) {
            synthesisStage = 2; // Stage 2: Writing sections
          } else if (elapsedSeconds < 75) {
            synthesisStage = 3; // Stage 3: Integration
          } else {
            synthesisStage = 4; // Stage 4: Quality check
          }
        }
        
        // Update progress
        setResearchProgress({
          stage: updatedTask.status as any,
          message: getProgressMessage(updatedTask.status, updatedTask.assigned_agent || 'agent', synthesisStage),
          synthesisStage,
        });

        // If completed or awaiting approval, extract results
        if (updatedTask.status === 'awaiting_approval' || updatedTask.status === 'approved') {
          if (updatedTask.ai_response) {
            setResearchMemo(updatedTask.ai_response);
          }
          
          // Extract cases if available in metadata
          if (updatedTask.metadata?.case_citations) {
            setCases(updatedTask.metadata.case_citations);
          }
          
          setIsResearching(false);
        }
        
        if (updatedTask.status === 'failed') {
          setIsResearching(false);
        }
      } catch (error) {
        console.error('Failed to poll task:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [currentTask?.id, currentTask?.status, researchStartTime]);

  const getProgressMessage = (status: string, agent: string, synthesisStage?: number) => {
    const stageMessages = {
      1: '📋 Stage 1: Organizing findings by topic...',
      2: '✍️ Stage 2: Writing memo sections in parallel...',
      3: '🔗 Stage 3: Integrating sections into cohesive memo...',
      4: '✅ Stage 4: Quality checking and finalizing...',
    };
    
    switch (status) {
      case 'pending':
        return 'Initializing research request...';
      case 'processing':
        if (synthesisStage && stageMessages[synthesisStage as keyof typeof stageMessages]) {
          return `🔍 ${agent} researching... ${stageMessages[synthesisStage as keyof typeof stageMessages]}`;
        }
        return `🔍 ${agent} is researching... Scraping case law and analyzing precedents`;
      case 'awaiting_approval':
        return '✅ Research complete! Review the memo below';
      case 'approved':
      case 'completed':
        return '✅ Research approved and saved';
      case 'failed':
        return '❌ Research failed. Please try again.';
      default:
        return '';
    }
  };

  const handleSubmitResearch = async () => {
    if (!question.trim()) return;

    setIsResearching(true);
    setResearchStartTime(Date.now()); // Track start time for synthesis progress
    setResearchProgress({ stage: 'pending', message: 'Submitting research request...' });
    setCases([]);
    setResearchMemo('');

    try {
      const result = await ingestTask({
        source: 'email',
        content: question,
        priority: priority,
      });

      // Immediately fetch the task to start polling
      const task = await getTask(result.task_id);
      setCurrentTask(task);
      setResearchProgress({
        stage: 'processing',
        message: 'Research in progress...',
      });
    } catch (error) {
      console.error('Failed to submit research:', error);
      setResearchProgress({
        stage: 'failed',
        message: 'Failed to submit research request',
      });
      setIsResearching(false);
    }
  };

  const handleApprove = async () => {
    if (!currentTask) return;

    try {
      await approveTask(currentTask.id, {
        approved: true,
        send_immediately: false,
      });
      
      const updatedTask = await getTask(currentTask.id);
      setCurrentTask(updatedTask);
      setResearchProgress({
        stage: 'completed',
        message: '✅ Research approved and saved',
      });
    } catch (error) {
      console.error('Failed to approve task:', error);
    }
  };

  const handleReject = () => {
    // Reset to allow new research
    setCurrentTask(null);
    setResearchProgress({ stage: 'idle', message: '' });
    setIsResearching(false);
    setResearchStartTime(null);
    setCases([]);
    setResearchMemo('');
  };

  const handleViewCase = (caseData: CaseData) => {
    setSelectedCase(caseData);
    setCaseDialogOpen(true);
  };

  const handleNewResearch = () => {
    setQuestion('');
    setCurrentTask(null);
    setResearchProgress({ stage: 'idle', message: '' });
    setIsResearching(false);
    setResearchStartTime(null);
    setCases([]);
    setResearchMemo('');
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <PsychologyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'text.primary' }}>
            AI Legal Researcher
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Ask a legal research question and watch our AI researcher find relevant case law in real-time
        </Typography>
      </Box>

      {/* Research Input Form */}
      <Card sx={{ mb: 3, boxShadow: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Research Question
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your legal research question here... (e.g., 'Research premises liability cases involving slip and fall accidents with inadequate warning signs')"
            disabled={isResearching}
            sx={{ mb: 2 }}
          />

          {/* Sample Questions */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Quick start - try a sample question:
            </Typography>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              {sampleQuestions.map((sample, index) => (
                <Chip
                  key={index}
                  label={sample.substring(0, 50) + '...'}
                  onClick={() => !isResearching && setQuestion(sample)}
                  disabled={isResearching}
                  size="small"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Stack>
          </Box>

          {/* Priority Selection */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Priority:
            </Typography>
            <Stack direction="row" spacing={1}>
              {(['high', 'medium', 'low'] as const).map((p) => (
                <Chip
                  key={p}
                  label={p.toUpperCase()}
                  color={priority === p ? 'primary' : 'default'}
                  onClick={() => !isResearching && setPriority(p)}
                  disabled={isResearching}
                />
              ))}
            </Stack>
          </Box>

          {/* Submit Button */}
          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={isResearching ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
            onClick={handleSubmitResearch}
            disabled={!question.trim() || isResearching}
            sx={{
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
              bgcolor: 'primary.main',
              '&:hover': { bgcolor: 'primary.dark' },
            }}
          >
            {isResearching ? 'Researching...' : 'Start Research'}
          </Button>
        </CardContent>
      </Card>

      {/* Research Progress */}
      {researchProgress.stage !== 'idle' && (
        <Card sx={{ mb: 3, boxShadow: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              {isResearching && <CircularProgress size={24} />}
              {researchProgress.stage === 'awaiting_approval' && <CheckCircleIcon color="success" />}
              {researchProgress.stage === 'completed' && <CheckCircleIcon color="success" />}
              {researchProgress.stage === 'failed' && <ErrorIcon color="error" />}
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {researchProgress.message}
              </Typography>
            </Box>
            
            {isResearching && <LinearProgress sx={{ mb: 2 }} />}
            
            {/* Multi-Stage Synthesis Progress Stepper */}
            {researchProgress.synthesisStage && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: 'primary.main' }}>
                  🔬 Multi-Stage Synthesis Pipeline
                </Typography>
                <Stepper activeStep={researchProgress.synthesisStage - 1} alternativeLabel>
                  <Step>
                    <StepLabel>Organize Findings</StepLabel>
                  </Step>
                  <Step>
                    <StepLabel>Write Sections</StepLabel>
                  </Step>
                  <Step>
                    <StepLabel>Integration</StepLabel>
                  </Step>
                  <Step>
                    <StepLabel>Quality Check</StepLabel>
                  </Step>
                </Stepper>
              </Box>
            )}
            
            {currentTask && (
              <Stack direction="row" spacing={2}>
                <Chip
                  icon={<GavelIcon />}
                  label={`Agent: ${currentTask.assigned_agent || 'Unknown'}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={`Status: ${currentTask.status}`}
                  size="small"
                  color={currentTask.status === 'failed' ? 'error' : 'default'}
                />
                {currentTask.metadata?.total_cases_found !== undefined && (
                  <Chip
                    icon={<SpeedIcon />}
                    label={`${currentTask.metadata.total_cases_found} cases found`}
                    size="small"
                    color="success"
                  />
                )}
              </Stack>
            )}
          </CardContent>
        </Card>
      )}

      {/* Found Cases */}
      {cases.length > 0 && (
        <Card sx={{ mb: 3, boxShadow: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <GavelIcon color="primary" />
              Relevant Cases Found ({cases.length})
            </Typography>
            
            <Stack spacing={2}>
              {cases.map((caseData, index) => (
                <Paper key={index} sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {index + 1}. {caseData.case_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Citation:</strong> {caseData.citation}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Court:</strong> {caseData.court} | <strong>Date:</strong> {caseData.date_filed}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {caseData.snippet.substring(0, 200)}...
                      </Typography>
                    </Box>
                    <Box>
                      <Tooltip title="View full case details">
                        <IconButton size="small" onClick={() => handleViewCase(caseData)} color="primary">
                          <DescriptionIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Open on CourtListener">
                        <IconButton
                          size="small"
                          component="a"
                          href={caseData.url}
                          target="_blank"
                          color="primary"
                        >
                          <LinkIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Research Memo */}
      {researchMemo && (
        <Card sx={{ mb: 3, boxShadow: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <DescriptionIcon color="primary" />
                Legal Research Memo
              </Typography>
              
              {researchProgress.stage === 'awaiting_approval' && (
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<ThumbDownIcon />}
                    onClick={handleReject}
                  >
                    Reject
                  </Button>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<ThumbUpIcon />}
                    onClick={handleApprove}
                  >
                    Approve
                  </Button>
                </Stack>
              )}
              
              {researchProgress.stage === 'completed' && (
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={handleNewResearch}
                >
                  New Research
                </Button>
              )}
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{
              bgcolor: 'grey.50',
              p: 3,
              borderRadius: 1,
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              maxHeight: 600,
              overflow: 'auto',
            }}>
              <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                {researchMemo}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Case Details Dialog */}
      <Dialog
        open={caseDialogOpen}
        onClose={() => setCaseDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {selectedCase?.case_name}
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          {selectedCase && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Citation
                </Typography>
                <Typography variant="body1">{selectedCase.citation}</Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Court
                </Typography>
                <Typography variant="body1">{selectedCase.court}</Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Date Filed
                </Typography>
                <Typography variant="body1">{selectedCase.date_filed}</Typography>
              </Box>
              
              <Divider />
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600, mb: 1 }}>
                  Summary
                </Typography>
                <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                  {selectedCase.snippet}
                </Typography>
              </Box>
              
              <Box>
                <Button
                  variant="outlined"
                  startIcon={<LinkIcon />}
                  component="a"
                  href={selectedCase.url}
                  target="_blank"
                  fullWidth
                >
                  View Full Opinion on CourtListener
                </Button>
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCaseDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LegalResearcher;
