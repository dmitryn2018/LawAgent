import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material'
import { Description, Download, Edit } from '@mui/icons-material'
import { templatesApi } from '../api'
import { Template, FormField } from '../types'
import MarkdownContent from '../components/MarkdownContent'

export default function TemplatesPage() {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [formData, setFormData] = useState<Record<string, unknown>>({})
  const [useAI, setUseAI] = useState(false)
  const [rendering, setRendering] = useState(false)
  const [error, setError] = useState('')
  const [renderedText, setRenderedText] = useState('')
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  
  useEffect(() => {
    loadTemplates()
  }, [])
  
  const loadTemplates = async () => {
    try {
      const data = await templatesApi.list()
      setTemplates(data.items)
    } catch (error) {
      console.error('Failed to load templates:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSelectTemplate = (template: Template) => {
    setSelectedTemplate(template)
    setFormData({})
    setRenderedText('')
    setDownloadUrl(null)
    setError('')
    
    // Initialize form data with defaults
    const initialData: Record<string, unknown> = {}
    template.form_schema.fields.forEach((field) => {
      if (field.default !== undefined) {
        initialData[field.name] = field.default
      } else if (field.type === 'checkbox') {
        initialData[field.name] = false
      } else {
        initialData[field.name] = ''
      }
    })
    setFormData(initialData)
  }
  
  const handleFieldChange = (fieldName: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }))
  }
  
  const handleRender = async () => {
    if (!selectedTemplate) return
    
    // Validate required fields
    const missingFields = selectedTemplate.form_schema.fields
      .filter(f => f.required && !formData[f.name])
      .map(f => f.label)
    
    if (missingFields.length > 0) {
      setError(`Заполните обязательные поля: ${missingFields.join(', ')}`)
      return
    }
    
    setRendering(true)
    setError('')
    
    try {
      const result = await templatesApi.render(selectedTemplate.id, {
        form_data: formData,
        use_ai_generation: useAI,
      })
      
      setRenderedText(result.rendered_text)
      if (result.file_id) {
        setDownloadUrl(templatesApi.getDownloadUrl(selectedTemplate.id, result.file_id))
      }
    } catch (error) {
      console.error('Failed to render template:', error)
      setError('Ошибка при генерации документа')
    } finally {
      setRendering(false)
    }
  }
  
  const handleOpenInEditor = () => {
    // Convert markdown to HTML for TipTap editor
    const htmlContent = convertMarkdownToHtml(renderedText)
    sessionStorage.setItem('editorContent', htmlContent)
    navigate('/editor')
    handleClose()
  }
  
  // Simple markdown to HTML converter for basic formatting
  const convertMarkdownToHtml = (markdown: string): string => {
    let html = markdown
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    
    // Italic
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>')
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>')
    html = '<p>' + html + '</p>'
    
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '')
    html = html.replace(/<p>\s*<\/p>/g, '')
    
    return html
  }
  
  const handleClose = () => {
    setSelectedTemplate(null)
    setFormData({})
    setRenderedText('')
    setDownloadUrl(null)
    setError('')
    setUseAI(false)
  }
  
  const renderFormField = (field: FormField) => {
    switch (field.type) {
      case 'text':
        return (
          <TextField
            key={field.name}
            fullWidth
            label={field.label}
            required={field.required}
            placeholder={field.placeholder}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            margin="normal"
          />
        )
      case 'textarea':
        return (
          <TextField
            key={field.name}
            fullWidth
            multiline
            rows={3}
            label={field.label}
            required={field.required}
            placeholder={field.placeholder}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            margin="normal"
          />
        )
      case 'select':
        return (
          <FormControl key={field.name} fullWidth margin="normal" required={field.required}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={formData[field.name] || ''}
              label={field.label}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
            >
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>{option}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )
      case 'checkbox':
        return (
          <FormControlLabel
            key={field.name}
            control={
              <Checkbox
                checked={Boolean(formData[field.name])}
                onChange={(e) => handleFieldChange(field.name, e.target.checked)}
              />
            }
            label={field.label}
          />
        )
      case 'date':
        return (
          <TextField
            key={field.name}
            fullWidth
            type="date"
            label={field.label}
            required={field.required}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            margin="normal"
            InputLabelProps={{ shrink: true }}
          />
        )
      default:
        return null
    }
  }
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Шаблоны документов
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Выберите шаблон для создания документа
      </Typography>
      
      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} sm={6} md={4} key={template.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Description color="primary" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h6">{template.name}</Typography>
                    {template.category && (
                      <Chip label={template.category} size="small" />
                    )}
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {template.description || 'Нет описания'}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => handleSelectTemplate(template)}
                >
                  Создать документ
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {/* Template form dialog */}
      <Dialog
        open={Boolean(selectedTemplate)}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        {selectedTemplate && (
          <>
            <DialogTitle>
              {selectedTemplate.name}
              {selectedTemplate.description && (
                <Typography variant="body2" color="text.secondary">
                  {selectedTemplate.description}
                </Typography>
              )}
            </DialogTitle>
            <DialogContent dividers>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              
              {!renderedText ? (
                <>
                  {selectedTemplate.form_schema.fields.map((field) => renderFormField(field))}
                  
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={useAI}
                        onChange={(e) => setUseAI(e.target.checked)}
                      />
                    }
                    label="Использовать AI для генерации описательных частей"
                    sx={{ mt: 2 }}
                  />
                </>
              ) : (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Сгенерированный документ:
                  </Typography>
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      maxHeight: 400,
                      overflow: 'auto',
                    }}
                  >
                    <MarkdownContent>
                      {renderedText}
                    </MarkdownContent>
                  </Box>
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={handleClose}>Отмена</Button>
              {!renderedText ? (
                <Button
                  variant="contained"
                  onClick={handleRender}
                  disabled={rendering}
                >
                  {rendering ? <CircularProgress size={24} /> : 'Сгенерировать'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setRenderedText('')}>
                    Изменить данные
                  </Button>
                  {downloadUrl && (
                    <Button
                      variant="outlined"
                      startIcon={<Download />}
                      href={downloadUrl}
                      target="_blank"
                    >
                      Скачать DOCX
                    </Button>
                  )}
                  <Button
                    variant="contained"
                    startIcon={<Edit />}
                    onClick={handleOpenInEditor}
                  >
                    Открыть в редакторе
                  </Button>
                </>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  )
}

