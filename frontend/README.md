# AI Legal Tender - Frontend Dashboard

A modern, responsive React dashboard for the AI Legal Tender platform - an intelligent legal automation system that orchestrates AI agents to handle law firm communications.

## 🎯 Overview

This frontend showcases the complete workflow of the AI Legal Tender system:
- **Inbox**: View incoming emails, texts, and call transcripts
- **Approval Queue**: Review and edit AI-generated responses before sending
- **AI Agents**: Monitor 5 specialist agents processing tasks in parallel
- **Outreach Monitor**: Track automated emails, SMS, and voice calls
- **Dashboard**: Real-time system stats and performance metrics

## 🏗️ Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Charts**: Recharts

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (or compatible runtime)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx        # Main dashboard with stats
│   │   ├── InboxView.tsx        # Incoming communications
│   │   ├── ApprovalQueue.tsx    # Review/edit AI responses
│   │   ├── AgentsView.tsx       # AI agent monitoring
│   │   ├── OutreachMonitor.tsx  # Sent communications tracker
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   └── Header.tsx           # Top header bar
│   ├── types.ts                 # TypeScript interfaces
│   ├── mockData.ts              # Demo data for presentation
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 Features

### 1. Dashboard
- Real-time system metrics (tasks, completion, response times)
- AMD MI300X inference speed monitoring
- Active agents overview
- Tech stack visualization (AMD + Google ADK + vLLM)

### 2. Inbox
- Unified view of all incoming communications
- Source indicators (📧 email, 💬 text, 📞 call)
- Status badges (pending, processing, awaiting approval)
- Task type classification
- Agent assignment tracking

### 3. Approval Queue
- Review AI-generated responses
- **Edit capability** - lawyers can modify AI drafts before approval
- Approve or reject workflows
- Outreach type indicators (email/SMS/voice)
- Client information display

### 4. AI Agents
- 5 specialist agents:
  - 💬 **Client Communication Guru** - Empathetic responses
  - 📋 **Records Wrangler** - Medical records requests
  - ⚖️ **Legal Researcher** - Case law & precedents
  - 📁 **Evidence Sorter** - Document categorization
  - 📅 **Voice Bot Scheduler** - Appointment management
- Performance metrics per agent
- Processing time stats

### 5. Outreach Monitor
- Track sent emails, SMS, and voice calls
- Delivery status tracking
- ElevenLabs voice call playback (demo)
- Multi-modal outreach stats

## 🎨 Design System

### Colors

```css
/* Primary */
primary-500: #0ea5e9

/* AMD Red */
amd-red: #ED1C24

/* Google Blue */
google-blue: #4285F4

/* Status Colors */
pending: yellow-100/800
processing: blue-100/800
approved: green-100/800
sent: purple-100/800
```

### Components

All components use Tailwind's utility classes with custom components defined in `index.css`:
- `.card` - White background cards with shadow
- `.btn-primary` - Primary action buttons
- `.btn-success` - Approval buttons
- `.btn-danger` - Rejection buttons
- `.badge` - Status and type indicators

## 📊 Mock Data

The app currently uses mock data defined in `mockData.ts` for demonstration purposes. This includes:
- 5 sample tasks with various statuses
- 5 AI agents with performance metrics
- 3 outreach activities
- System-wide statistics

### Connecting to Real Backend

To connect to your actual backend:

1. Create an API service file:

```typescript
// src/services/api.ts
const API_BASE = process.env.VITE_API_URL || 'http://localhost:8000';

export const fetchTasks = async () => {
  const response = await fetch(`${API_BASE}/tasks`);
  return response.json();
};

export const approveTask = async (taskId: string) => {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/approve`, {
    method: 'POST',
  });
  return response.json();
};
```

2. Update components to use real data:

```typescript
// In ApprovalQueue.tsx
import { fetchTasks, approveTask } from '../services/api';

// Replace mockTasks with:
const [tasks, setTasks] = useState([]);

useEffect(() => {
  fetchTasks().then(setTasks);
}, []);
```

3. Add environment variables:

```bash
# .env
VITE_API_URL=http://your-amd-server:8000
```

## 🎯 Hackathon Demo Flow

### 3-Minute Demo Script

**Act 1: Show Messy Input (Inbox View)**
- Navigate to Inbox
- Point out real client message: "um, I wanted to check on my case... insurance company is saying they wont pay???"
- Show automatic classification: `client_communication`
- Show agent assignment: `communicator`

**Act 2: AI Processing (Dashboard)**
- Show system stats: `127 tokens/sec` on AMD MI300X
- Highlight tech stack: vLLM + ROCm + Google ADK
- Show agent activity metrics

**Act 3: Review & Approve (Approval Queue)**
- Open approval queue
- Show AI-generated professional response
- Demonstrate edit capability (click edit icon)
- Make a small change
- Click "Approve & Send"

**Act 4: Outreach (Outreach Monitor)**
- Show sent email
- Show SMS notification
- **Highlight ElevenLabs voice call** - "Generated by ElevenLabs Voice AI"

**Act 5: Impact Statement**
- "Lawyers stay in control, AI handles the grunt work"
- "Self-hosted on AMD = data never leaves your infrastructure"
- "Google ADK orchestrates parallel agents via A2A protocol"

## 🏆 Challenge Alignment

### Morgan & Morgan
✅ Handles messy legal communications
✅ Human-in-the-loop approval workflow
✅ Multi-channel outreach (email, SMS, voice)
✅ Practical value for personal injury law firms

### AMD
✅ Showcases MI300X compute power
✅ Displays vLLM inference speed (127 tok/s)
✅ ROCm stack visualization
✅ Self-hosted AI argument for data privacy

### Google Cloud
✅ Google ADK branding throughout UI
✅ Agent-to-Agent (A2A) protocol mentioned
✅ Continuous orchestration loop concept
✅ Multi-agent coordination visualization

## 🛠️ Customization

### Adding a New View

1. Create component in `src/components/NewView.tsx`
2. Add route in `App.tsx`:

```typescript
<Route path="/new-view" element={<NewView />} />
```

3. Add nav item in `Sidebar.tsx`:

```typescript
{ path: '/new-view', icon: Icon, label: 'New View' }
```

### Modifying Mock Data

Edit `src/mockData.ts` to change:
- Task examples
- Agent descriptions
- System metrics
- Outreach activities

### Theming

Update `tailwind.config.js` to customize colors:

```javascript
theme: {
  extend: {
    colors: {
      primary: { ... },
      amd: { ... },
      google: { ... }
    }
  }
}
```

## 📝 Notes

- All TypeScript errors are expected before running `npm install`
- The app is fully responsive (mobile, tablet, desktop)
- No backend required for demo - uses mock data
- Production build optimized with Vite
- Tailwind CSS provides utility-first styling

## 🚀 Deployment

### Vercel
```bash
npm run build
vercel --prod
```

### Netlify
```bash
npm run build
netlify deploy --prod --dir=dist
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

## 📄 License

Created for AI Legal Tender - Triple Challenge Hackathon Entry

---

**Built with ❤️ for Morgan & Morgan + AMD + Google Cloud Hackathon**
