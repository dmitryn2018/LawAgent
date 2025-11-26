import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material'
import {
  Search,
  Add,
  Delete,
  ExpandMore,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  HourglassEmpty,
  Refresh,
  Business,
  Person,
} from '@mui/icons-material'
import { ddApi } from '../api'
import { DDCheck } from '../types'
import MarkdownContent from '../components/MarkdownContent'

const CHECK_TYPES = [
  { value: 'ma_dd', label: 'M&A Due Diligence' },
  { value: 'compliance', label: 'Комплаенс / Санкции' },
]

const JURISDICTIONS = [
  { value: 'RU', label: 'Россия' },
  { value: 'EU', label: 'ЕС' },
  { value: 'UK', label: 'Великобритания' },
]

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'error'
    default: return 'default'
  }
}

const getRiskLabel = (risk: string) => {
  switch (risk) {
    case 'low': return 'Низкий'
    case 'medium': return 'Средний'
    case 'high': return 'Высокий'
    default: return risk
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return <CheckCircle color="success" />
    case 'processing': return <HourglassEmpty color="info" />
    case 'failed': return <ErrorIcon color="error" />
    default: return <HourglassEmpty color="disabled" />
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

export default function DueDiligencePage() {
  const { checkId } = useParams()
  const navigate = useNavigate()
  
  const [checks, setChecks] = useState<DDCheck[]>([])
  const [selectedCheck, setSelectedCheck] = useState<DDCheck | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  
  // Form state
  const [companyName, setCompanyName] = useState('')
  const [checkType, setCheckType] = useState('ma_dd')
  const [jurisdiction, setJurisdiction] = useState('RU')
  const [error, setError] = useState('')
  
  useEffect(() => {
    loadChecks()
  }, [])
  
  useEffect(() => {
    if (checkId) {
      loadCheck(parseInt(checkId))
    } else {
      setSelectedCheck(null)
    }
  }, [checkId])
  
  // Poll for status updates
  useEffect(() => {
    if (selectedCheck && (selectedCheck.status === 'pending' || selectedCheck.status === 'processing')) {
      const interval = setInterval(() => {
        loadCheck(selectedCheck.id)
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [selectedCheck])
  
  const loadChecks = async () => {
    try {
      const data = await ddApi.list()
      setChecks(data.items)
    } catch (error) {
      console.error('Failed to load checks:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadCheck = async (id: number) => {
    try {
      const check = await ddApi.get(id)
      setSelectedCheck(check)
      
      // Update in list
      setChecks(prev => prev.map(c => c.id === id ? check : c))
    } catch (error) {
      console.error('Failed to load check:', error)
    }
  }
  
  const handleCreateCheck = async () => {
    if (!companyName.trim()) {
      setError('Введите название компании')
      return
    }
    
    setCreating(true)
    setError('')
    
    try {
      const check = await ddApi.create({
        company_name: companyName,
        check_type: checkType,
        jurisdiction,
      })
      
      setChecks([check, ...checks])
      setCompanyName('')
      navigate(`/due-diligence/${check.id}`)
    } catch (error) {
      console.error('Failed to create check:', error)
      setError('Ошибка при создании проверки')
    } finally {
      setCreating(false)
    }
  }
  
  const handleDeleteCheck = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await ddApi.delete(id)
      setChecks(checks.filter(c => c.id !== id))
      if (selectedCheck?.id === id) {
        navigate('/due-diligence')
      }
    } catch (error) {
      console.error('Failed to delete check:', error)
    }
  }
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Due Diligence проверки
      </Typography>
      
      <Grid container spacing={3}>
        {/* Left column - form and list */}
        <Grid item xs={12} md={4}>
          {/* Create form */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Новая проверка
              </Typography>
              
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              
              <TextField
                fullWidth
                label="Название компании"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                margin="normal"
                placeholder='например: ООО "Тест"'
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Тип проверки</InputLabel>
                <Select
                  value={checkType}
                  label="Тип проверки"
                  onChange={(e) => setCheckType(e.target.value)}
                >
                  {CHECK_TYPES.map((t) => (
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
                  {JURISDICTIONS.map((j) => (
                    <MenuItem key={j.value} value={j.value}>{j.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <Button
                fullWidth
                variant="contained"
                startIcon={creating ? <CircularProgress size={20} color="inherit" /> : <Search />}
                onClick={handleCreateCheck}
                disabled={creating}
                sx={{ mt: 2 }}
              >
                Запустить проверку
              </Button>
            </CardContent>
          </Card>
          
          {/* Checks list */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                История проверок
              </Typography>
              
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : checks.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  Нет проведённых проверок
                </Typography>
              ) : (
                <Box>
                  {checks.map((check) => (
                    <Paper
                      key={check.id}
                      sx={{
                        p: 2,
                        mb: 1,
                        cursor: 'pointer',
                        bgcolor: selectedCheck?.id === check.id ? 'primary.light' : 'background.paper',
                        color: selectedCheck?.id === check.id ? 'white' : 'text.primary',
                        '&:hover': {
                          bgcolor: selectedCheck?.id === check.id ? 'primary.light' : 'grey.100',
                        },
                      }}
                      onClick={() => navigate(`/due-diligence/${check.id}`)}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box>
                          <Typography variant="subtitle2">
                            {check.company_name}
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.8 }}>
                            {CHECK_TYPES.find(t => t.value === check.check_type)?.label}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(check.status)}
                          <IconButton
                            size="small"
                            onClick={(e) => handleDeleteCheck(check.id, e)}
                            sx={{ color: 'inherit' }}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Right column - results */}
        <Grid item xs={12} md={8}>
          {selectedCheck ? (
            <CheckResults check={selectedCheck} onRefresh={() => loadCheck(selectedCheck.id)} />
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Search sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Выберите проверку или создайте новую
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

function CheckResults({ check, onRefresh }: { check: DDCheck; onRefresh: () => void }) {
  const [viewMode, setViewMode] = useState<'partner' | 'junior'>('partner')

  if (check.status === 'pending' || check.status === 'processing') {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="h6">
          Проверка выполняется...
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Это может занять несколько минут
        </Typography>
      </Paper>
    )
  }
  
  if (check.status === 'failed') {
    return (
      <Paper sx={{ p: 4 }}>
        <Alert severity="error">
          Ошибка при выполнении проверки: {check.error_message || 'Неизвестная ошибка'}
        </Alert>
      </Paper>
    )
  }

  // Filter risks based on view mode
  const getFilteredRisks = () => {
    if (!check.risk_items) return []
    if (viewMode === 'junior') return check.risk_items
    
    // Partner mode: only critical risks (deal_breakers and high severity)
    return check.risk_items
      .filter(r => r.severity === 'high' || r.impact_on_deal === 'deal_breaker')
      .slice(0, 5)
  }

  const filteredRisks = getFilteredRisks()
  
  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h5">{check.company_name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {CHECK_TYPES.find(t => t.value === check.check_type)?.label} •{' '}
              {JURISDICTIONS.find(j => j.value === check.jurisdiction)?.label} •{' '}
              {check.completed_at && new Date(check.completed_at).toLocaleString('ru-RU')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
            <IconButton onClick={onRefresh}>
              <Refresh />
            </IconButton>
          </Box>
        </Box>
        
        {/* Risk indicators */}
        {check.risk_indicators && (
          <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={check.risk_indicators.overall === 'high' ? <Warning /> : <CheckCircle />}
              label={`Общий риск: ${getRiskLabel(check.risk_indicators.overall)}`}
              color={getRiskColor(check.risk_indicators.overall) as 'success' | 'warning' | 'error'}
              size="medium"
            />
            <Chip
              label={`Юридический: ${getRiskLabel(check.risk_indicators.legal)}`}
              color={getRiskColor(check.risk_indicators.legal) as 'success' | 'warning' | 'error'}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`Финансовый: ${getRiskLabel(check.risk_indicators.financial)}`}
              color={getRiskColor(check.risk_indicators.financial) as 'success' | 'warning' | 'error'}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`Регуляторный: ${getRiskLabel(check.risk_indicators.regulatory)}`}
              color={getRiskColor(check.risk_indicators.regulatory) as 'success' | 'warning' | 'error'}
              variant="outlined"
              size="small"
            />
          </Box>
        )}
      </Paper>
      
      {/* AI Summary */}
      {check.ai_summary && (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Аналитический отчёт
          </Typography>
          <MarkdownContent>
            {check.ai_summary}
          </MarkdownContent>
        </Paper>
      )}
      
      {/* Risk items */}
      {filteredRisks.length > 0 && (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            {viewMode === 'partner' 
              ? `Критические риски (${filteredRisks.length} из ${check.risk_items?.length || 0})`
              : `Выявленные риски (${check.risk_items?.length || 0})`
            }
          </Typography>
          {filteredRisks.map((item, idx) => {
            const impactBadge = getImpactBadge(item.impact_on_deal)
            return (
              <Box key={idx} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
                  <Chip
                    label={getRiskLabel(item.severity)}
                    size="small"
                    color={getRiskColor(item.severity) as 'success' | 'warning' | 'error'}
                  />
                  {impactBadge && (
                    <Chip
                      label={impactBadge.label}
                      size="small"
                      color={impactBadge.color}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  )}
                </Box>
                <MarkdownContent sx={{ fontWeight: 600, fontSize: '0.875rem', mb: 0.5 }}>
                  {item.title}
                </MarkdownContent>
                <MarkdownContent sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
                  {item.description}
                </MarkdownContent>
                {idx < filteredRisks.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            )
          })}
        </Paper>
      )}
      
      {/* Raw data - only in junior mode */}
      {viewMode === 'junior' && check.raw_data && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography>Исходные данные</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <RawDataDisplay data={check.raw_data} />
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  )
}

function RawDataDisplay({ data }: { data: Record<string, unknown> }) {
  // Translation map for field names
  const fieldLabels: Record<string, string> = {
    // Company info
    name: 'Название',
    inn: 'ИНН',
    ogrn: 'ОГРН',
    registration_date: 'Дата регистрации',
    legal_address: 'Юридический адрес',
    authorized_capital: 'Уставный капитал',
    status: 'Статус',
    main_activity: 'Основной вид деятельности',
    // Court cases
    case_number: 'Номер дела',
    court: 'Суд',
    role: 'Роль',
    claim_amount: 'Сумма иска',
    subject: 'Предмет',
    date_filed: 'Дата подачи',
    // Debts
    tax_debt: 'Налоговая задолженность',
    social_fund_debt: 'Задолженность в соцфонды',
    enforcement_proceedings: 'Исполнительные производства',
    number: 'Номер',
    amount: 'Сумма',
    type: 'Тип',
    // Licenses
    valid_until: 'Действует до',
    // Beneficial owners
    share: 'Доля',
    position: 'Должность',
    // Financials
    revenue_2023: 'Выручка 2023',
    revenue_2022: 'Выручка 2022',
    profit_2023: 'Прибыль 2023',
    profit_2022: 'Прибыль 2022',
    assets: 'Активы',
    // Sanctions
    ofac_list: 'Список OFAC',
    eu_sanctions: 'Санкции ЕС',
    un_sanctions: 'Санкции ООН',
    national_list: 'Национальный список',
    // Sections
    company_info: 'Информация о компании',
    court_cases: 'Судебные дела',
    debts: 'Задолженности',
    licenses: 'Лицензии',
    regions: 'Регионы',
    sanctions_flags: 'Санкционные проверки',
    beneficial_owners: 'Бенефициары',
    financials: 'Финансовые показатели',
    red_flags: 'Красные флаги',
  }

  const translateKey = (key: string): string => {
    return fieldLabels[key] || key.replace(/_/g, ' ')
  }

  const formatValue = (v: unknown): string => {
    if (v === null || v === undefined) return '-'
    if (typeof v === 'boolean') return v ? 'Да' : 'Нет'
    if (typeof v === 'object') {
      // Format nested objects nicely
      if (Array.isArray(v)) {
        if (v.length === 0) return '-'
        return v.map(item => {
          if (typeof item === 'object' && item !== null) {
            // Format object fields as readable text
            return Object.entries(item as Record<string, unknown>)
              .map(([k, val]) => `${translateKey(k)}: ${val}`)
              .join(', ')
          }
          return String(item)
        }).join(' | ')
      }
      return Object.entries(v as Record<string, unknown>)
        .map(([k, val]) => `${translateKey(k)}: ${val}`)
        .join(', ')
    }
    return String(v)
  }

  const renderSection = (key: string, value: unknown) => {
    if (Array.isArray(value)) {
      if (value.length === 0) return null
      
      // Check if it's an array of strings (like red_flags)
      if (typeof value[0] === 'string') {
        return (
          <Box key={key} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              {translateKey(key)}
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  {value.map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{String(item)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )
      }
      
      // Array of objects
      if (typeof value[0] === 'object' && value[0] !== null) {
        return (
          <Box key={key} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              {translateKey(key)}
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(value[0] as Record<string, unknown>).map((col) => (
                      <TableCell key={col}>
                        {translateKey(col)}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {value.map((row, idx) => (
                    <TableRow key={idx}>
                      {Object.values(row as Record<string, unknown>).map((cell, cellIdx) => (
                        <TableCell key={cellIdx}>
                          {formatValue(cell)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )
      }
      
      return null
    }
    
    if (typeof value === 'object' && value !== null) {
      return (
        <Box key={key} sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            {translateKey(key)}
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableBody>
                {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                  <TableRow key={k}>
                    <TableCell sx={{ fontWeight: 500 }}>
                      {translateKey(k)}
                    </TableCell>
                    <TableCell>
                      {formatValue(v)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )
    }
    
    return null
  }
  
  return (
    <Box>
      {Object.entries(data).map(([key, value]) => renderSection(key, value))}
    </Box>
  )
}

