import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Stack,
  Chip,
  Divider,
  IconButton,
  Toolbar,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

interface DocumentData {
  title: string;
  type: string;
  content: string;
  createdAt: string;
  lastModified: string;
}

const DocumentEditor: React.FC = () => {
  const { title, type } = useParams<{ title: string; type: string }>();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState<DocumentData>({
    title: decodeURIComponent(title || 'Untitled Document'),
    type: decodeURIComponent(type || 'other'),
    content: getTemplateContent(decodeURIComponent(type || 'other')),
    createdAt: new Date().toISOString(),
    lastModified: new Date().toISOString(),
  });

  const [isEditing, setIsEditing] = useState(true);

  function getTemplateContent(docType: string): string {
    const templates: Record<string, string> = {
      demand_letter: `[Law Firm Letterhead]

[Date]

[Insurance Company Name]
[Claims Department]
[Address]

Re: Demand for Settlement
    Claimant: [Client Name]
    Claim Number: [Claim #]
    Date of Loss: [Date]

Dear Claims Adjuster:

This firm represents [Client Name] regarding injuries sustained in [describe incident] on [date].

FACTS:
[Describe the incident and circumstances]

INJURIES:
[List and describe injuries sustained]

DAMAGES:
[Itemize damages including medical expenses, lost wages, pain and suffering]

DEMAND:
We hereby demand settlement in the amount of $[amount] to resolve all claims arising from this incident.

Please respond within 30 days.

Sincerely,

[Attorney Name]
[Law Firm]`,
      
      settlement_agreement: `SETTLEMENT AGREEMENT

This Settlement Agreement ("Agreement") is entered into as of [Date] by and between:

PARTY A: [Name]
PARTY B: [Name]

RECITALS:
WHEREAS, a dispute has arisen between the parties concerning [describe dispute];
WHEREAS, the parties desire to resolve this dispute amicably;

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the parties agree as follows:

1. PAYMENT: Party A shall pay Party B the sum of $[amount] in full settlement.

2. RELEASE: Upon receipt of payment, Party B releases Party A from all claims.

3. CONFIDENTIALITY: The terms of this Agreement shall remain confidential.

4. BINDING EFFECT: This Agreement shall be binding upon the parties and their successors.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

_______________________     _______________________
Party A                      Party B`,

      complaint: `IN THE [COURT NAME]
[COUNTY/JURISDICTION]

[Plaintiff Name],               )
                 Plaintiff,     ) Case No. [Case Number]
                                )
v.                              ) COMPLAINT
                                )
[Defendant Name],               )
                 Defendant.     )

COMES NOW the Plaintiff, by and through undersigned counsel, and for their Complaint states:

JURISDICTION AND VENUE
1. This Court has jurisdiction over this matter pursuant to [statute/authority].
2. Venue is proper in this Court pursuant to [statute/authority].

PARTIES
3. Plaintiff is [description].
4. Defendant is [description].

FACTUAL ALLEGATIONS
5. On or about [date], [describe events].

CAUSES OF ACTION
COUNT I - [Cause of Action]
[Allegations]

WHEREFORE, Plaintiff requests judgment against Defendant for:
a) Compensatory damages;
b) Costs of this action;
c) Such other relief as the Court deems just and proper.

Respectfully submitted,

_______________________
[Attorney Name]
Attorney for Plaintiff`,

      motion: `IN THE [COURT NAME]
[COUNTY/JURISDICTION]

[Case Caption],                 ) Case No. [Case Number]
                                )
                 Plaintiff,     ) MOTION TO [Title]
                                )
v.                              )
                                )
                 Defendant.     )

MOTION
COMES NOW [Party Name], by and through undersigned counsel, and respectfully moves this Court for an Order [describe relief sought].

MEMORANDUM IN SUPPORT
I. INTRODUCTION
[Brief overview]

II. FACTUAL BACKGROUND
[Relevant facts]

III. LEGAL ARGUMENT
[Legal authorities and argument]

IV. CONCLUSION
For the foregoing reasons, [Party] respectfully requests that this Court grant this Motion.

Respectfully submitted,

_______________________
[Attorney Name]
Attorney for [Party]`,

      medical_records_request: `MEDICAL RECORDS REQUEST

[Date]

[Medical Provider Name]
Medical Records Department
[Address]

Re: Authorization for Release of Medical Records
    Patient: [Patient Name]
    DOB: [Date of Birth]
    SSN: [Last 4 digits]

Dear Medical Records Department:

I hereby authorize the release of my complete medical records to:

[Law Firm Name]
[Address]

This authorization includes all records from [start date] through [end date], including but not limited to:
• Office visit notes
• Test results and laboratory reports
• X-rays, MRI, CT scans (copies or CD)
• Surgical reports
• Prescription records
• Billing statements

Please provide an itemized billing statement for all services rendered.

I understand this authorization may be revoked at any time by written notice, except to the extent that action has already been taken in reliance thereon.

Patient Signature: _______________________  Date: _______
Print Name: _______________________

Please contact our office at [phone] with any questions.

Thank you for your prompt attention to this matter.`,

      memo: `MEMORANDUM

TO:      [Recipient]
FROM:    [Your Name]
DATE:    [Date]
RE:      [Subject Matter]

QUESTION PRESENTED
[State the legal question]

BRIEF ANSWER
[Provide concise answer]

FACTS
[State relevant facts]

DISCUSSION
I. [First Issue]
[Analysis with legal authorities]

II. [Second Issue]
[Analysis with legal authorities]

CONCLUSION
[Summarize conclusion and recommendations]`,

      contract: `AGREEMENT

This Agreement is made as of [Date] between:

PARTY A: [Name and Address]
PARTY B: [Name and Address]

RECITALS
[Background and purpose]

AGREEMENT
NOW, THEREFORE, in consideration of the mutual covenants contained herein, the parties agree:

1. SCOPE OF SERVICES
[Description of services/goods]

2. COMPENSATION
[Payment terms]

3. TERM
[Duration of agreement]

4. TERMINATION
[Termination conditions]

5. CONFIDENTIALITY
[Confidentiality provisions]

6. GOVERNING LAW
This Agreement shall be governed by the laws of [State].

7. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties.

IN WITNESS WHEREOF, the parties have executed this Agreement.

_______________________     _______________________
Party A                      Party B
Date: _________________     Date: _________________`,

      other: `[Document Title]

[Start writing your document here...]



`,
    };

    return templates[docType] || templates.other;
  }

  const handleSave = () => {
    // Here you would integrate with your backend to save the document
    console.log('Saving document:', document);
    alert('Document saved successfully!');
    setDocument({ ...document, lastModified: new Date().toISOString() });
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    const elem = window.document.createElement('a');
    const file = new Blob([document.content], { type: 'text/plain' });
    elem.href = URL.createObjectURL(file);
    elem.download = `${document.title}.txt`;
    window.document.body.appendChild(elem);
    elem.click();
    window.document.body.removeChild(elem);
  };

  const getDocumentTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      demand_letter: 'Demand Letter',
      settlement_agreement: 'Settlement Agreement',
      complaint: 'Complaint',
      motion: 'Motion',
      medical_records_request: 'Medical Records Request',
      memo: 'Legal Memo',
      contract: 'Contract',
      other: 'Document',
    };
    return labels[type] || 'Document';
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <IconButton onClick={() => navigate('/')} sx={{ color: 'primary.main' }}>
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#3a434e' }}>
              {document.title}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
              <Chip
                label={getDocumentTypeLabel(document.type)}
                size="small"
                color="primary"
                sx={{ bgcolor: '#8a6d4f' }}
              />
              <Typography variant="caption" color="text.secondary">
                Created: {new Date(document.createdAt).toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                • Last Modified: {new Date(document.lastModified).toLocaleString()}
              </Typography>
            </Stack>
          </Box>
        </Stack>

        {/* Toolbar */}
        <Card sx={{ bgcolor: '#f5f5f5' }}>
          <Toolbar sx={{ gap: 1 }}>
            <Button
              variant={isEditing ? 'contained' : 'outlined'}
              startIcon={<EditIcon />}
              onClick={() => setIsEditing(!isEditing)}
              sx={{
                bgcolor: isEditing ? '#8a6d4f' : 'transparent',
                '&:hover': { bgcolor: isEditing ? '#6d5640' : 'rgba(138, 109, 79, 0.1)' },
              }}
            >
              {isEditing ? 'Editing' : 'Preview'}
            </Button>
            <Divider orientation="vertical" flexItem />
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              sx={{
                borderColor: '#059669',
                color: '#059669',
                '&:hover': { borderColor: '#047857', bgcolor: 'rgba(5, 150, 105, 0.1)' },
              }}
            >
              Save
            </Button>
            <Button
              variant="outlined"
              startIcon={<PrintIcon />}
              onClick={handlePrint}
            >
              Print
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownload}
            >
              Download
            </Button>
            <Button
              variant="outlined"
              startIcon={<ShareIcon />}
              onClick={() => alert('Share functionality would be implemented here')}
            >
              Share
            </Button>
          </Toolbar>
        </Card>
      </Box>

      {/* Document Content */}
      <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 4 }}>
          {isEditing ? (
            <TextField
              fullWidth
              multiline
              value={document.content}
              onChange={(e) => setDocument({ ...document, content: e.target.value })}
              variant="outlined"
              sx={{
                flex: 1,
                '& .MuiOutlinedInput-root': {
                  height: '100%',
                  alignItems: 'flex-start',
                  fontFamily: 'monospace',
                  fontSize: '0.95rem',
                  lineHeight: 1.8,
                },
                '& textarea': {
                  height: '100% !important',
                },
              }}
            />
          ) : (
            <Box
              sx={{
                flex: 1,
                whiteSpace: 'pre-wrap',
                fontFamily: 'serif',
                fontSize: '1rem',
                lineHeight: 1.8,
                p: 3,
                bgcolor: 'white',
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                overflow: 'auto',
              }}
            >
              {document.content}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DocumentEditor;
