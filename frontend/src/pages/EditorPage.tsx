import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Chip,
  CircularProgress,
  Divider,
  TextField,
  InputAdornment,
  Alert,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
} from '@mui/material'
import {
  FormatBold,
  FormatItalic,
  FormatUnderlined,
  FormatListBulleted,
  FormatListNumbered,
  FormatAlignLeft,
  FormatAlignCenter,
  FormatAlignRight,
  Undo,
  Redo,
  Search,
  Analytics,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Email,
  ContentCopy,
  VerifiedUser,
  PendingActions,
  Person,
  Business,
} from '@mui/icons-material'
import { analysisApi, clausesApi, documentsApi } from '../api'
import { DocumentAnalysisResponse, DocumentRisk, Clause, SavedAnalysis } from '../types'
import MarkdownContent from '../components/MarkdownContent'

// Hash function for document text
const hashText = async (text: string): Promise<string> => {
  const encoder = new TextEncoder()
  const data = encoder.encode(text)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

export default function EditorPage() {
  const { documentId } = useParams()
  const [tabValue, setTabValue] = useState(0)
  const [analyzing, setAnalyzing] = useState(false)
  const [loadingDocument, setLoadingDocument] = useState(false)
  const [analysis, setAnalysis] = useState<DocumentAnalysisResponse | null>(null)
  const [savedAnalysis, setSavedAnalysis] = useState<SavedAnalysis | null>(null)
  const [clauses, setClauses] = useState<Clause[]>([])
  const [clauseSearch, setClauseSearch] = useState('')
  const [loadingClauses, setLoadingClauses] = useState(false)
  const [error, setError] = useState('')
  const [viewMode, setViewMode] = useState<'partner' | 'junior'>('partner')
  const [clientLetterOpen, setClientLetterOpen] = useState(false)
  const [clientLetter, setClientLetter] = useState('')
  const [generatingLetter, setGeneratingLetter] = useState(false)
  const [savingAnalysis, setSavingAnalysis] = useState(false)
  
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Highlight.configure({
        multicolor: true,
      }),
    ],
    content: sessionStorage.getItem('editorContent') || '<p>Вставьте или введите текст документа для анализа...</p>',
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-xl focus:outline-none min-h-[500px] p-4',
      },
    },
  })
  
  useEffect(() => {
    sessionStorage.removeItem('editorContent')
  }, [])

  // Load document by ID from URL
  useEffect(() => {
    if (documentId && editor) {
      const loadDocument = async () => {
        setLoadingDocument(true)
        try {
          const doc = await documentsApi.get(parseInt(documentId))
          if (doc.content) {
            editor.commands.setContent(doc.content)
          }
        } catch (err) {
          console.error('Failed to load document:', err)
          setError('Не удалось загрузить документ')
        } finally {
          setLoadingDocument(false)
        }
      }
      loadDocument()
    }
  }, [documentId, editor])
  
  useEffect(() => {
    loadClauses()
  }, [clauseSearch])
  
  const loadClauses = async () => {
    setLoadingClauses(true)
    try {
      const data = await clausesApi.list({
        search: clauseSearch || undefined,
        page_size: 20,
      })
      setClauses(data.items)
    } catch (error) {
      console.error('Failed to load clauses:', error)
    } finally {
      setLoadingClauses(false)
    }
  }
  
  const handleAnalyze = async () => {
    if (!editor) return
    
    const text = editor.getText()
    if (text.length < 100) {
      setError('Текст документа должен содержать минимум 100 символов')
      return
    }
    
    setAnalyzing(true)
    setError('')
    
    try {
      const result = await analysisApi.analyzeDocument({ text })
      setAnalysis(result)
      setTabValue(0)
      highlightRisks(result.risks)
      
      // Try to save analysis
      const textHash = await hashText(text)
      try {
        const saved = await analysisApi.saveAnalysis({
          document_text_hash: textHash,
          analysis_data: result
        })
        setSavedAnalysis(saved)
      } catch (e) {
        console.error('Failed to save analysis:', e)
      }
    } catch (error) {
      console.error('Failed to analyze document:', error)
      setError('Ошибка при анализе документа')
    } finally {
      setAnalyzing(false)
    }
  }
  
  const handleMarkReviewed = async () => {
    if (!savedAnalysis) return
    
    setSavingAnalysis(true)
    try {
      const updated = await analysisApi.markReviewed(savedAnalysis.id)
      setSavedAnalysis(updated)
    } catch (error) {
      console.error('Failed to mark as reviewed:', error)
    } finally {
      setSavingAnalysis(false)
    }
  }
  
  const handleGenerateClientLetter = async () => {
    if (!analysis) return
    
    setGeneratingLetter(true)
    setClientLetterOpen(true)
    
    try {
      const result = await analysisApi.generateClientLetter({
        summary: analysis.summary,
        risks: analysis.risks,
        deal_impact: analysis.deal_impact,
        language: 'ru'
      })
      setClientLetter(result.letter_text)
    } catch (error) {
      console.error('Failed to generate letter:', error)
      setClientLetter('Ошибка при генерации письма')
    } finally {
      setGeneratingLetter(false)
    }
  }
  
  const handleCopyLetter = () => {
    navigator.clipboard.writeText(clientLetter)
  }
  
  const highlightRisks = useCallback((risks: DocumentRisk[]) => {
    if (!editor) return
    editor.chain().focus().unsetHighlight().run()
    const text = editor.getText()
    risks.forEach((risk) => {
      risk.spans.forEach((span) => {
        if (span.start_char >= 0 && span.end_char <= text.length) {
          const riskText = text.substring(span.start_char, span.end_char)
          if (riskText) {
            console.log('Highlighting:', riskText.substring(0, 50))
          }
        }
      })
    })
  }, [editor])
  
  const handleInsertClause = (clause: Clause) => {
    if (!editor) return
    editor.chain().focus().insertContent(`\n\n${clause.body}\n\n`).run()
  }
  
  const getRiskIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <ErrorIcon color="error" fontSize="small" />
      case 'medium': return <Warning color="warning" fontSize="small" />
      case 'low': return <CheckCircle color="success" fontSize="small" />
      default: return null
    }
  }

  const getRiskLevelBadge = (level: string) => {
    switch (level) {
      case 'high': return { color: 'error' as const, label: '🔴 Высокий риск', icon: <ErrorIcon /> }
      case 'medium': return { color: 'warning' as const, label: '🟡 Средний риск', icon: <Warning /> }
      case 'low': return { color: 'success' as const, label: '🟢 Низкий риск', icon: <CheckCircle /> }
      default: return { color: 'default' as const, label: 'Не определён', icon: null }
    }
  }

  const getImpactBadge = (impact?: string) => {
    switch (impact) {
      case 'deal_breaker': return { color: 'error' as const, label: 'Deal-breaker' }
      case 'negotiable': return { color: 'warning' as const, label: 'Торгуемо' }
      case 'cosmetic': return { color: 'default' as const, label: 'Косметика' }
      default: return null
    }
  }

  // Filter risks based on view mode
  const getFilteredRisks = () => {
    if (!analysis) return []
    if (viewMode === 'junior') return analysis.risks
    
    // Partner mode: top 3 critical risks
    return analysis.risks
      .filter(r => r.severity === 'high' || r.impact_on_deal === 'deal_breaker')
      .slice(0, 3)
      .concat(
        analysis.risks
          .filter(r => r.severity !== 'high' && r.impact_on_deal !== 'deal_breaker')
          .slice(0, Math.max(0, 3 - analysis.risks.filter(r => r.severity === 'high' || r.impact_on_deal === 'deal_breaker').length))
      )
      .slice(0, 3)
  }
  
  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 100px)', gap: 2 }}>
      {/* Editor area */}
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Toolbar */}
        <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
          <Tooltip title="Отменить">
            <IconButton size="small" onClick={() => editor?.chain().focus().undo().run()}>
              <Undo />
            </IconButton>
          </Tooltip>
          <Tooltip title="Повторить">
            <IconButton size="small" onClick={() => editor?.chain().focus().redo().run()}>
              <Redo />
            </IconButton>
          </Tooltip>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Tooltip title="Жирный">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().toggleBold().run()}
              color={editor?.isActive('bold') ? 'primary' : 'default'}
            >
              <FormatBold />
            </IconButton>
          </Tooltip>
          <Tooltip title="Курсив">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().toggleItalic().run()}
              color={editor?.isActive('italic') ? 'primary' : 'default'}
            >
              <FormatItalic />
            </IconButton>
          </Tooltip>
          <Tooltip title="Подчёркнутый">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().toggleUnderline().run()}
              color={editor?.isActive('underline') ? 'primary' : 'default'}
            >
              <FormatUnderlined />
            </IconButton>
          </Tooltip>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Tooltip title="Маркированный список">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().toggleBulletList().run()}
              color={editor?.isActive('bulletList') ? 'primary' : 'default'}
            >
              <FormatListBulleted />
            </IconButton>
          </Tooltip>
          <Tooltip title="Нумерованный список">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().toggleOrderedList().run()}
              color={editor?.isActive('orderedList') ? 'primary' : 'default'}
            >
              <FormatListNumbered />
            </IconButton>
          </Tooltip>
          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
          <Tooltip title="По левому краю">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().setTextAlign('left').run()}
              color={editor?.isActive({ textAlign: 'left' }) ? 'primary' : 'default'}
            >
              <FormatAlignLeft />
            </IconButton>
          </Tooltip>
          <Tooltip title="По центру">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().setTextAlign('center').run()}
              color={editor?.isActive({ textAlign: 'center' }) ? 'primary' : 'default'}
            >
              <FormatAlignCenter />
            </IconButton>
          </Tooltip>
          <Tooltip title="По правому краю">
            <IconButton
              size="small"
              onClick={() => editor?.chain().focus().setTextAlign('right').run()}
              color={editor?.isActive({ textAlign: 'right' }) ? 'primary' : 'default'}
            >
              <FormatAlignRight />
            </IconButton>
          </Tooltip>
          <Box sx={{ flexGrow: 1 }} />
          <Button
            variant="contained"
            startIcon={analyzing ? <CircularProgress size={20} color="inherit" /> : <Analytics />}
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            Анализировать
          </Button>
        </Box>

        {/* Risk Level Badge & Review Status */}
        {analysis && (
          <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <Chip
              icon={getRiskLevelBadge(analysis.overall_risk_level).icon || undefined}
              label={getRiskLevelBadge(analysis.overall_risk_level).label}
              color={getRiskLevelBadge(analysis.overall_risk_level).color}
              size="medium"
            />
            
            {savedAnalysis && (
              <>
                <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
                {savedAnalysis.review_status === 'reviewed' ? (
                  <Chip
                    icon={<VerifiedUser />}
                    label={`Проверено: ${savedAnalysis.reviewed_by?.full_name || savedAnalysis.reviewed_by?.email || 'Юрист'}, ${savedAnalysis.reviewed_at ? new Date(savedAnalysis.reviewed_at).toLocaleDateString('ru-RU') : ''}`}
                    color="success"
                    size="small"
                  />
                ) : (
                  <>
                    <Chip
                      icon={<PendingActions />}
                      label="Не проверено"
                      color="default"
                      size="small"
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={handleMarkReviewed}
                      disabled={savingAnalysis}
                    >
                      Отметить как проверено
                    </Button>
                  </>
                )}
              </>
            )}

            <Box sx={{ flexGrow: 1 }} />
            
            <Button
              size="small"
              variant="outlined"
              startIcon={<Email />}
              onClick={handleGenerateClientLetter}
            >
              Письмо клиенту
            </Button>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" onClose={() => setError('')} sx={{ mx: 2, mt: 1 }}>
            {error}
          </Alert>
        )}
        
        {/* Editor content */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            '& .ProseMirror': {
              minHeight: '100%',
              outline: 'none',
              p: 3,
              '& p': { margin: '0.5em 0' },
              '& h1, h2, h3': { margin: '1em 0 0.5em' },
              '& ul, ol': { paddingLeft: '1.5em' },
            },
          }}
        >
          <EditorContent editor={editor} />
        </Box>
      </Paper>
      
      {/* Side panel */}
      <Paper sx={{ width: 400, display: 'flex', flexDirection: 'column' }}>
        {/* View Mode Toggle */}
        <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="partner">
              <Business sx={{ mr: 0.5 }} fontSize="small" />
              Партнёр
            </ToggleButton>
            <ToggleButton value="junior">
              <Person sx={{ mr: 0.5 }} fontSize="small" />
              Джун
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Tabs
          value={tabValue}
          onChange={(_, v) => setTabValue(v)}
          variant="fullWidth"
        >
          <Tab label="Саммари" />
          <Tab label="Риски" />
          <Tab label="Сделка" />
          <Tab label="Клаузы" />
        </Tabs>
        
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {tabValue === 0 && (
            <SummaryTab analysis={analysis} viewMode={viewMode} />
          )}
          {tabValue === 1 && (
            <RisksTab 
              analysis={analysis} 
              getRiskIcon={getRiskIcon} 
              getImpactBadge={getImpactBadge}
              filteredRisks={getFilteredRisks()}
              viewMode={viewMode}
            />
          )}
          {tabValue === 2 && (
            <DealImpactTab analysis={analysis} />
          )}
          {tabValue === 3 && (
            <ClausesTab
              clauses={clauses}
              search={clauseSearch}
              onSearchChange={setClauseSearch}
              loading={loadingClauses}
              onInsert={handleInsertClause}
            />
          )}
        </Box>
      </Paper>

      {/* Client Letter Dialog */}
      <Dialog open={clientLetterOpen} onClose={() => setClientLetterOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Письмо клиенту</DialogTitle>
        <DialogContent>
          {generatingLetter ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Card variant="outlined" sx={{ mt: 1 }}>
              <CardContent>
                <MarkdownContent>{clientLetter}</MarkdownContent>
              </CardContent>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClientLetterOpen(false)}>Закрыть</Button>
          <Button 
            variant="contained" 
            startIcon={<ContentCopy />}
            onClick={handleCopyLetter}
            disabled={generatingLetter}
          >
            Скопировать
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

function SummaryTab({ analysis, viewMode }: { analysis: DocumentAnalysisResponse | null; viewMode: string }) {
  if (!analysis) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
        Нажмите "Анализировать" для получения саммари документа
      </Typography>
    )
  }
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Краткое содержание
      </Typography>
      <MarkdownContent sx={{ mb: 3 }}>
        {analysis.summary}
      </MarkdownContent>
      
      {analysis.parties && analysis.parties.length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom>
            Стороны:
          </Typography>
          <List dense sx={{ mb: 2 }}>
            {analysis.parties.map((party, idx) => (
              <ListItem key={idx} sx={{ py: 0.5, pl: 0 }}>
                <ListItemText 
                  primary={`• ${party}`} 
                  primaryTypographyProps={{ variant: 'body2' }} 
                />
              </ListItem>
            ))}
          </List>
        </>
      )}
      
      {viewMode === 'junior' && analysis.key_terms && analysis.key_terms.length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom>
            Ключевые условия:
          </Typography>
          <List dense>
            {analysis.key_terms.map((term, idx) => (
              <ListItem key={idx} sx={{ py: 0 }}>
                <ListItemText primary={`• ${term}`} primaryTypographyProps={{ variant: 'body2' }} />
              </ListItem>
            ))}
          </List>
        </>
      )}
      
      {viewMode === 'junior' && analysis.recommendations && analysis.recommendations.length > 0 && (
        <>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Рекомендации:
          </Typography>
          <List dense>
            {analysis.recommendations.map((rec, idx) => (
              <ListItem key={idx} sx={{ py: 0 }}>
                <ListItemText primary={`${idx + 1}. ${rec}`} primaryTypographyProps={{ variant: 'body2' }} />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  )
}

function RisksTab({
  analysis,
  getRiskIcon,
  getImpactBadge,
  filteredRisks,
  viewMode,
}: {
  analysis: DocumentAnalysisResponse | null
  getRiskIcon: (severity: string) => React.ReactNode
  getImpactBadge: (impact?: string) => { color: 'error' | 'warning' | 'default'; label: string } | null
  filteredRisks: DocumentRisk[]
  viewMode: string
}) {
  if (!analysis) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
        Нажмите "Анализировать" для выявления рисков
      </Typography>
    )
  }
  
  const risksToShow = viewMode === 'partner' ? filteredRisks : analysis.risks
  
  if (risksToShow.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CheckCircle color="success" sx={{ fontSize: 48, mb: 1 }} />
        <Typography variant="body2" color="text.secondary">
          Значительных рисков не выявлено
        </Typography>
      </Box>
    )
  }
  
  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        {viewMode === 'partner' 
          ? `Топ-${risksToShow.length} критических рисков (всего: ${analysis.risks.length})`
          : `Выявлено рисков: ${analysis.risks.length}`
        }
      </Typography>
      <List>
        {risksToShow.map((risk) => {
          const impactBadge = getImpactBadge(risk.impact_on_deal)
          return (
            <ListItem
              key={risk.id}
              sx={{
                flexDirection: 'column',
                alignItems: 'flex-start',
                bgcolor: 'grey.50',
                borderRadius: 1,
                mb: 1,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
                {getRiskIcon(risk.severity)}
                {impactBadge && (
                  <Chip 
                    label={impactBadge.label} 
                    size="small" 
                    color={impactBadge.color}
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </Box>
              <MarkdownContent sx={{ fontWeight: 600, fontSize: '0.875rem', mb: 0.5 }}>
                {risk.title}
              </MarkdownContent>
              <MarkdownContent sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
                {risk.description}
              </MarkdownContent>
              {risk.recommendation && (
                <MarkdownContent sx={{ fontSize: '0.875rem', color: 'primary.main', mt: 1 }}>
                  💡 {risk.recommendation}
                </MarkdownContent>
              )}
            </ListItem>
          )
        })}
      </List>
    </Box>
  )
}

function DealImpactTab({ analysis }: { analysis: DocumentAnalysisResponse | null }) {
  if (!analysis) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
        Нажмите "Анализировать" для оценки влияния на сделку
      </Typography>
    )
  }

  if (!analysis.deal_impact) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
        Информация о влиянии на сделку недоступна
      </Typography>
    )
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        📌 Влияние на сделку
      </Typography>
      
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            💰 Цена
          </Typography>
          <MarkdownContent sx={{ fontSize: '0.875rem' }}>
            {analysis.deal_impact.price}
          </MarkdownContent>
        </CardContent>
      </Card>

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            🏗️ Структура
          </Typography>
          <MarkdownContent sx={{ fontSize: '0.875rem' }}>
            {analysis.deal_impact.structure}
          </MarkdownContent>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            🎯 Контроль/управление
          </Typography>
          <MarkdownContent sx={{ fontSize: '0.875rem' }}>
            {analysis.deal_impact.control}
          </MarkdownContent>
        </CardContent>
      </Card>
    </Box>
  )
}

function ClausesTab({
  clauses,
  search,
  onSearchChange,
  loading,
  onInsert,
}: {
  clauses: Clause[]
  search: string
  onSearchChange: (value: string) => void
  loading: boolean
  onInsert: (clause: Clause) => void
}) {
  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        placeholder="Поиск клауз..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={24} />
        </Box>
      ) : clauses.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
          Клаузы не найдены
        </Typography>
      ) : (
        <List dense>
          {clauses.map((clause) => (
            <ListItem key={clause.id} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => onInsert(clause)}
                sx={{ borderRadius: 1, bgcolor: 'grey.50' }}
              >
                <ListItemText
                  primary={clause.title}
                  secondary={
                    <>
                      <Chip label={clause.category} size="small" sx={{ mr: 0.5 }} />
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: 'block',
                          mt: 0.5,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {clause.body.substring(0, 100)}...
                      </Typography>
                    </>
                  }
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  )
}
