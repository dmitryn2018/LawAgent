import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Avatar,
  List,
  ListItemButton,
  ListItemText,
  Chip,
  Skeleton,
} from '@mui/material'
import {
  Chat,
  Description,
  Search,
  Edit,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { chatApi, ddApi, documentsApi } from '../api'
import { ChatSession, DDCheck, Document } from '../types'

const features = [
  {
    title: 'Чатбот юриста',
    description: 'Задавайте вопросы по праву и получайте ответы с ссылками на источники',
    icon: <Chat sx={{ fontSize: 40 }} />,
    path: '/chat',
    color: '#1a365d',
  },
  {
    title: 'Генератор документов',
    description: 'Создавайте документы по готовым шаблонам: NDA, SPA, трудовые договоры',
    icon: <Description sx={{ fontSize: 40 }} />,
    path: '/templates',
    color: '#2d4a7c',
  },
  {
    title: 'Due Diligence',
    description: 'Запускайте автоматизированные юридические проверки компаний',
    icon: <Search sx={{ fontSize: 40 }} />,
    path: '/due-diligence',
    color: '#38a169',
  },
  {
    title: 'Редактор с AI',
    description: 'Анализируйте документы, выявляйте риски и используйте клауз-банк',
    icon: <Edit sx={{ fontSize: 40 }} />,
    path: '/editor',
    color: '#c69c6d',
  },
]

const statusLabels: Record<string, { label: string; color: 'default' | 'primary' | 'success' | 'error' | 'warning' }> = {
  pending: { label: 'Ожидание', color: 'default' },
  processing: { label: 'Обработка', color: 'primary' },
  completed: { label: 'Готово', color: 'success' },
  failed: { label: 'Ошибка', color: 'error' },
}

const riskColors: Record<string, 'success' | 'warning' | 'error'> = {
  low: 'success',
  medium: 'warning',
  high: 'error',
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [recentChats, setRecentChats] = useState<ChatSession[]>([])
  const [recentChecks, setRecentChecks] = useState<DDCheck[]>([])
  const [recentDocs, setRecentDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [chatsRes, checksRes, docsRes] = await Promise.all([
          chatApi.listSessions(),
          ddApi.list({ page_size: 3 }),
          documentsApi.list({ page_size: 3 }),
        ])
        setRecentChats(chatsRes.items.slice(0, 3))
        setRecentChecks(checksRes.items)
        setRecentDocs(docsRes.items)
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
    })
  }
  
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Добро пожаловать, {user?.full_name || user?.email}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Выберите инструмент для работы
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid item xs={12} sm={6} md={3} key={feature.title}>
            <Card
              sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardActionArea
                onClick={() => navigate(feature.path)}
                sx={{ height: '100%', p: 2 }}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Avatar
                    sx={{
                      width: 80,
                      height: 80,
                      bgcolor: feature.color,
                      margin: '0 auto 16px',
                    }}
                  >
                    {feature.icon}
                  </Avatar>
                  <Typography variant="h6" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Box sx={{ mt: 6 }}>
        <Typography variant="h5" gutterBottom>
          Быстрые действия
        </Typography>
        <Grid container spacing={2}>
          {/* Последние чаты */}
          <Grid item xs={12} md={4}>
            <Card sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" fontWeight={500} gutterBottom>
                Последние чаты
              </Typography>
              {loading ? (
                <>
                  <Skeleton variant="text" height={40} />
                  <Skeleton variant="text" height={40} />
                </>
              ) : recentChats.length > 0 ? (
                <List dense disablePadding>
                  {recentChats.map((chat) => (
                    <ListItemButton
                      key={chat.id}
                      onClick={() => navigate(`/chat/${chat.id}`)}
                      sx={{ borderRadius: 1, px: 1 }}
                    >
                      <ListItemText
                        primary={chat.title || 'Без названия'}
                        secondary={formatDate(chat.updated_at)}
                        primaryTypographyProps={{ noWrap: true, variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Нет активных чатов. Начните новый диалог в разделе "Чатбот".
                </Typography>
              )}
            </Card>
          </Grid>

          {/* Последние проверки */}
          <Grid item xs={12} md={4}>
            <Card sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" fontWeight={500} gutterBottom>
                Последние проверки
              </Typography>
              {loading ? (
                <>
                  <Skeleton variant="text" height={40} />
                  <Skeleton variant="text" height={40} />
                </>
              ) : recentChecks.length > 0 ? (
                <List dense disablePadding>
                  {recentChecks.map((check) => (
                    <ListItemButton
                      key={check.id}
                      onClick={() => navigate(`/due-diligence/${check.id}`)}
                      sx={{ borderRadius: 1, px: 1 }}
                    >
                      <ListItemText
                        primary={check.company_name}
                        secondary={
                          <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mt: 0.5 }}>
                            <Chip
                              label={statusLabels[check.status]?.label || check.status}
                              color={statusLabels[check.status]?.color || 'default'}
                              size="small"
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                            {check.status === 'completed' && check.risk_indicators && (
                              <Chip
                                label={check.risk_indicators.overall === 'low' ? 'Низкий' : check.risk_indicators.overall === 'medium' ? 'Средний' : 'Высокий'}
                                color={riskColors[check.risk_indicators.overall]}
                                size="small"
                                variant="outlined"
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        }
                        primaryTypographyProps={{ noWrap: true, variant: 'body2' }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Нет проведённых проверок. Запустите новую в разделе "Проверки".
                </Typography>
              )}
            </Card>
          </Grid>

          {/* Последние документы */}
          <Grid item xs={12} md={4}>
            <Card sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle1" fontWeight={500} gutterBottom>
                Документы
              </Typography>
              {loading ? (
                <>
                  <Skeleton variant="text" height={40} />
                  <Skeleton variant="text" height={40} />
                </>
              ) : recentDocs.length > 0 ? (
                <List dense disablePadding>
                  {recentDocs.map((doc) => (
                    <ListItemButton
                      key={doc.id}
                      onClick={() => navigate(`/editor/${doc.id}`)}
                      sx={{ borderRadius: 1, px: 1 }}
                    >
                      <ListItemText
                        primary={doc.title}
                        secondary={`${doc.document_type} • ${formatDate(doc.created_at)}`}
                        primaryTypographyProps={{ noWrap: true, variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Создавайте документы через шаблоны или используйте редактор.
                </Typography>
              )}
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

