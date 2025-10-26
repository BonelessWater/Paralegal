import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import theme from './theme';
import { NotificationProvider } from './contexts/NotificationContext';
import Dashboard from './components/Dashboard';
import ApprovalQueue from './components/ApprovalQueue';
import AgentsView from './components/AgentsView';
import OutreachMonitor from './components/OutreachMonitor';
import InboxView from './components/InboxView';
import NotificationsView from './components/NotificationsView';
import SettingsView from './components/SettingsView';
import ProfileView from './components/ProfileView';
import DocumentEditor from './components/DocumentEditor';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <NotificationProvider>
        <BrowserRouter>
          <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
            <Sidebar isOpen={true} onClose={() => {}} />
            
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
              <Header />
              
              <Box
                component="main"
                sx={{
                  flexGrow: 1,
                  p: 3,
                  overflow: 'auto',
                  bgcolor: 'background.default',
                }}
              >
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/inbox" element={<InboxView />} />
                  <Route path="/approval" element={<ApprovalQueue />} />
                  <Route path="/history" element={<OutreachMonitor />} />
                  <Route path="/settings" element={<SettingsView />} />
                  <Route path="/agents" element={<AgentsView />} />
                  <Route path="/notifications" element={<NotificationsView />} />
                  <Route path="/profile" element={<ProfileView />} />
                  <Route path="/document/:title/:type" element={<DocumentEditor />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Box>
            </Box>
          </Box>
        </BrowserRouter>
      </NotificationProvider>
    </ThemeProvider>
  );
}

export default App;
