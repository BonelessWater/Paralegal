import { createTheme } from '@mui/material/styles';

// Professional law firm color palette
const theme = createTheme({
  palette: {
    primary: {
      main: '#8a6d4f', // Refined warm brown/gold
      light: '#b08356',
      dark: '#725843',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3a434e', // Professional navy blue
      light: '#5d7085',
      dark: '#2a313a',
      contrastText: '#ffffff',
    },
    background: {
      default: '#fafaf9',
      paper: '#ffffff',
    },
    text: {
      primary: '#1c1917',
      secondary: '#57534e',
    },
    success: {
      main: '#059669',
      light: '#10b981',
      dark: '#047857',
    },
    warning: {
      main: '#d97706',
      light: '#f59e0b',
      dark: '#b45309',
    },
    error: {
      main: '#dc2626',
      light: '#ef4444',
      dark: '#b91c1c',
    },
    info: {
      main: '#0284c7',
      light: '#0ea5e9',
      dark: '#0369a1',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.75,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: '0.02em',
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 2px 4px rgba(138, 109, 79, 0.1), 0 1px 2px rgba(138, 109, 79, 0.06)',
    '0 4px 8px rgba(138, 109, 79, 0.1), 0 2px 4px rgba(138, 109, 79, 0.06)',
    '0 8px 16px rgba(138, 109, 79, 0.1), 0 4px 8px rgba(138, 109, 79, 0.06)',
    '0 12px 24px rgba(138, 109, 79, 0.12), 0 6px 12px rgba(138, 109, 79, 0.08)',
    '0 16px 32px rgba(138, 109, 79, 0.12), 0 8px 16px rgba(138, 109, 79, 0.08)',
    '0 20px 40px rgba(138, 109, 79, 0.14), 0 10px 20px rgba(138, 109, 79, 0.1)',
    '0 24px 48px rgba(138, 109, 79, 0.14), 0 12px 24px rgba(138, 109, 79, 0.1)',
    '0 2px 8px rgba(58, 67, 78, 0.15)',
    '0 4px 12px rgba(58, 67, 78, 0.15)',
    '0 6px 16px rgba(58, 67, 78, 0.15)',
    '0 8px 20px rgba(58, 67, 78, 0.15)',
    '0 10px 24px rgba(58, 67, 78, 0.18)',
    '0 12px 28px rgba(58, 67, 78, 0.18)',
    '0 16px 32px rgba(58, 67, 78, 0.2)',
    '0 20px 40px rgba(58, 67, 78, 0.2)',
    '0 24px 48px rgba(58, 67, 78, 0.22)',
    '0 28px 56px rgba(58, 67, 78, 0.22)',
    '0 32px 64px rgba(58, 67, 78, 0.24)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          padding: '8px 20px',
          fontSize: '0.9375rem',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          },
        },
        contained: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #8a6d4f 0%, #725843 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #725843 0%, #5f4a3a 100%)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
          },
          transition: 'box-shadow 0.2s ease-in-out',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)',
        },
        elevation2: {
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '2px 0 8px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          fontSize: '0.8125rem',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
        },
        head: {
          fontWeight: 600,
          backgroundColor: '#f5f5f4',
          color: '#44403c',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: '#b08356',
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginBottom: 4,
          '&.Mui-selected': {
            backgroundColor: 'rgba(138, 109, 79, 0.12)',
            borderLeft: '4px solid #8a6d4f',
            paddingLeft: '12px',
            '&:hover': {
              backgroundColor: 'rgba(138, 109, 79, 0.18)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(138, 109, 79, 0.08)',
          },
        },
      },
    },
  },
});

export default theme;
