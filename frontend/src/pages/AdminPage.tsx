import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Add,
  Delete,
  Refresh,
  CloudUpload,
  Edit,
} from '@mui/icons-material'
import { documentsApi, clausesApi } from '../api'
import { Document, Clause } from '../types'

const DOCUMENT_TYPES = [
  { value: 'internal_case', label: 'Внутреннее дело' },
  { value: 'external_law', label: 'Законодательство' },
  { value: 'case_law', label: 'Судебная практика' },
  { value: 'memo', label: 'Мемо' },
  { value: 'template', label: 'Шаблон' },
]

const JURISDICTIONS = [
  { value: 'RU', label: 'Россия' },
  { value: 'EU', label: 'ЕС' },
  { value: 'UK', label: 'Великобритания' },
  { value: 'US', label: 'США' },
  { value: 'INTERNAL', label: 'Внутренняя практика' },
]

const PRACTICE_AREAS = [
  { value: 'M&A', label: 'M&A' },
  { value: 'Litigation', label: 'Судебные споры' },
  { value: 'Corporate', label: 'Корпоративное право' },
  { value: 'Labor', label: 'Трудовое право' },
  { value: 'Compliance', label: 'Комплаенс' },
  { value: 'IP', label: 'Интеллектуальная собственность' },
]

const CLAUSE_CATEGORIES = [
  'arbitration',
  'force_majeure',
  'confidentiality',
  'liability',
  'termination',
  'governing_law',
  'representations',
  'indemnification',
]

export default function AdminPage() {
  const [tabValue, setTabValue] = useState(0)
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Администрирование
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Документы" />
          <Tab label="Клаузы" />
        </Tabs>
      </Paper>
      
      {tabValue === 0 && <DocumentsTab />}
      {tabValue === 1 && <ClausesTab />}
    </Box>
  )
}

function DocumentsTab() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  
  // Upload form
  const [uploadOpen, setUploadOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [documentType, setDocumentType] = useState('')
  const [jurisdiction, setJurisdiction] = useState('')
  const [practiceArea, setPracticeArea] = useState('')
  
  useEffect(() => {
    loadDocuments()
  }, [])
  
  const loadDocuments = async () => {
    try {
      const data = await documentsApi.list({ page_size: 100 })
      setDocuments(data.items)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setTitle(file.name.replace(/\.[^.]+$/, ''))
      setUploadOpen(true)
    }
  }
  
  const handleUpload = async () => {
    if (!selectedFile || !title || !documentType) {
      setError('Заполните обязательные поля')
      return
    }
    
    setUploading(true)
    setError('')
    
    try {
      await documentsApi.upload(selectedFile, {
        title,
        document_type: documentType,
        jurisdiction: jurisdiction || undefined,
        practice_area: practiceArea || undefined,
      })
      
      handleCloseUpload()
      loadDocuments()
    } catch (error) {
      console.error('Failed to upload document:', error)
      setError('Ошибка при загрузке документа')
    } finally {
      setUploading(false)
    }
  }
  
  const handleCloseUpload = () => {
    setUploadOpen(false)
    setSelectedFile(null)
    setTitle('')
    setDocumentType('')
    setJurisdiction('')
    setPracticeArea('')
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }
  
  const handleDelete = async (id: number) => {
    if (!confirm('Удалить документ?')) return
    
    try {
      await documentsApi.delete(id)
      setDocuments(documents.filter(d => d.id !== id))
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }
  
  const handleReindex = async (id: number) => {
    try {
      await documentsApi.reindex(id)
      loadDocuments()
    } catch (error) {
      console.error('Failed to reindex document:', error)
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'indexed': return 'success'
      case 'pending': return 'warning'
      case 'processing': return 'info'
      case 'failed': return 'error'
      default: return 'default'
    }
  }
  
  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
        />
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={() => fileInputRef.current?.click()}
        >
          Загрузить документ
        </Button>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadDocuments}
        >
          Обновить
        </Button>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Название</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Юрисдикция</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.title}</TableCell>
                  <TableCell>
                    {DOCUMENT_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type}
                  </TableCell>
                  <TableCell>{doc.jurisdiction || '—'}</TableCell>
                  <TableCell>
                    <Chip
                      label={doc.indexing_status}
                      size="small"
                      color={getStatusColor(doc.indexing_status) as 'success' | 'warning' | 'info' | 'error'}
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(doc.created_at).toLocaleDateString('ru-RU')}
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => handleReindex(doc.id)} title="Переиндексировать">
                      <Refresh />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(doc.id)} color="error" title="Удалить">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Upload dialog */}
      <Dialog open={uploadOpen} onClose={handleCloseUpload} maxWidth="sm" fullWidth>
        <DialogTitle>Загрузка документа</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Файл: {selectedFile?.name}
          </Typography>
          
          <TextField
            fullWidth
            label="Название"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
            required
          />
          
          <FormControl fullWidth margin="normal" required>
            <InputLabel>Тип документа</InputLabel>
            <Select
              value={documentType}
              label="Тип документа"
              onChange={(e) => setDocumentType(e.target.value)}
            >
              {DOCUMENT_TYPES.map((t) => (
                <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Юрисдикция</InputLabel>
            <Select
              value={jurisdiction}
              label="Юрисдикция"
              onChange={(e) => setJurisdiction(e.target.value)}
            >
              <MenuItem value="">—</MenuItem>
              {JURISDICTIONS.map((j) => (
                <MenuItem key={j.value} value={j.value}>{j.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Практика</InputLabel>
            <Select
              value={practiceArea}
              label="Практика"
              onChange={(e) => setPracticeArea(e.target.value)}
            >
              <MenuItem value="">—</MenuItem>
              {PRACTICE_AREAS.map((p) => (
                <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUpload}>Отмена</Button>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? <CircularProgress size={24} /> : 'Загрузить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

function ClausesTab() {
  const [clauses, setClauses] = useState<Clause[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingClause, setEditingClause] = useState<Clause | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  
  // Form state
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [category, setCategory] = useState('')
  const [clauseJurisdiction, setClauseJurisdiction] = useState('')
  const [pracArea, setPracArea] = useState('')
  const [notes, setNotes] = useState('')
  
  useEffect(() => {
    loadClauses()
  }, [])
  
  const loadClauses = async () => {
    try {
      const data = await clausesApi.list({ page_size: 100 })
      setClauses(data.items)
    } catch (error) {
      console.error('Failed to load clauses:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleOpenCreate = () => {
    setEditingClause(null)
    setTitle('')
    setBody('')
    setCategory('')
    setClauseJurisdiction('')
    setPracArea('')
    setNotes('')
    setDialogOpen(true)
  }
  
  const handleOpenEdit = (clause: Clause) => {
    setEditingClause(clause)
    setTitle(clause.title)
    setBody(clause.body)
    setCategory(clause.category)
    setClauseJurisdiction(clause.jurisdiction || '')
    setPracArea(clause.practice_area || '')
    setNotes(clause.notes || '')
    setDialogOpen(true)
  }
  
  const handleClose = () => {
    setDialogOpen(false)
    setEditingClause(null)
    setError('')
  }
  
  const handleSave = async () => {
    if (!title || !body || !category) {
      setError('Заполните обязательные поля')
      return
    }
    
    setSaving(true)
    setError('')
    
    try {
      const data = {
        title,
        body,
        category,
        jurisdiction: clauseJurisdiction || null,
        practice_area: pracArea || null,
        notes: notes || null,
        language: 'ru',
        tags: null,
      }
      
      if (editingClause) {
        await clausesApi.update(editingClause.id, data)
      } else {
        await clausesApi.create(data)
      }
      
      handleClose()
      loadClauses()
    } catch (error) {
      console.error('Failed to save clause:', error)
      setError('Ошибка при сохранении')
    } finally {
      setSaving(false)
    }
  }
  
  const handleDelete = async (id: number) => {
    if (!confirm('Удалить клаузу?')) return
    
    try {
      await clausesApi.delete(id)
      setClauses(clauses.filter(c => c.id !== id))
    } catch (error) {
      console.error('Failed to delete clause:', error)
    }
  }
  
  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleOpenCreate}
        >
          Добавить клаузу
        </Button>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Название</TableCell>
                <TableCell>Категория</TableCell>
                <TableCell>Юрисдикция</TableCell>
                <TableCell>Практика</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clauses.map((clause) => (
                <TableRow key={clause.id}>
                  <TableCell>{clause.title}</TableCell>
                  <TableCell>
                    <Chip label={clause.category} size="small" />
                  </TableCell>
                  <TableCell>{clause.jurisdiction || '—'}</TableCell>
                  <TableCell>{clause.practice_area || '—'}</TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => handleOpenEdit(clause)}>
                      <Edit />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(clause.id)} color="error">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Create/Edit dialog */}
      <Dialog open={dialogOpen} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingClause ? 'Редактировать клаузу' : 'Новая клауза'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="Название"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            margin="normal"
            required
          />
          
          <TextField
            fullWidth
            multiline
            rows={6}
            label="Текст клаузы"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            margin="normal"
            required
          />
          
          <FormControl fullWidth margin="normal" required>
            <InputLabel>Категория</InputLabel>
            <Select
              value={category}
              label="Категория"
              onChange={(e) => setCategory(e.target.value)}
            >
              {CLAUSE_CATEGORIES.map((c) => (
                <MenuItem key={c} value={c}>{c}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Юрисдикция</InputLabel>
            <Select
              value={clauseJurisdiction}
              label="Юрисдикция"
              onChange={(e) => setClauseJurisdiction(e.target.value)}
            >
              <MenuItem value="">—</MenuItem>
              {JURISDICTIONS.map((j) => (
                <MenuItem key={j.value} value={j.value}>{j.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Практика</InputLabel>
            <Select
              value={pracArea}
              label="Практика"
              onChange={(e) => setPracArea(e.target.value)}
            >
              <MenuItem value="">—</MenuItem>
              {PRACTICE_AREAS.map((p) => (
                <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            multiline
            rows={2}
            label="Заметки"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Отмена</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? <CircularProgress size={24} /> : 'Сохранить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

