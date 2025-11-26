import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  IconButton,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Card,
  CardContent,
} from '@mui/material'
import {
  Send,
  Add,
  Delete,
  ExpandMore,
  Person,
  SmartToy,
} from '@mui/icons-material'
import { chatApi } from '../api'
import { ChatSession, ChatMessage, SourceReference } from '../types'
import MarkdownContent from '../components/MarkdownContent'

const JURISDICTIONS = [
  { value: 'RU', label: 'Россия' },
  { value: 'EU', label: 'ЕС' },
  { value: 'UK', label: 'Великобритания' },
  { value: 'US', label: 'США' },
  { value: 'INTERNAL', label: 'Внутренняя практика' },
]

const MODES = [
  { value: 'question', label: 'Вопрос по праву' },
  { value: 'case_review', label: 'Обзор дела' },
  { value: 'case_search', label: 'Поиск похожих кейсов' },
]

export default function ChatPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [jurisdiction, setJurisdiction] = useState('RU')
  const [mode, setMode] = useState('question')
  const [sessionsLoading, setSessionsLoading] = useState(true)
  
  useEffect(() => {
    loadSessions()
  }, [])
  
  useEffect(() => {
    if (sessionId) {
      loadMessages(parseInt(sessionId))
    } else {
      setMessages([])
    }
  }, [sessionId])
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  const loadSessions = async () => {
    try {
      const data = await chatApi.listSessions()
      setSessions(data.items)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setSessionsLoading(false)
    }
  }
  
  const loadMessages = async (id: number) => {
    try {
      const data = await chatApi.getMessages(id)
      setMessages(data)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }
  
  const handleNewSession = async () => {
    try {
      const session = await chatApi.createSession({
        jurisdiction,
        mode,
      })
      setSessions([session, ...sessions])
      navigate(`/chat/${session.id}`)
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }
  
  const handleDeleteSession = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await chatApi.deleteSession(id)
      setSessions(sessions.filter(s => s.id !== id))
      if (sessionId && parseInt(sessionId) === id) {
        navigate('/chat')
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }
  
  const handleSend = async () => {
    if (!input.trim() || loading) return
    
    let currentSessionId = sessionId ? parseInt(sessionId) : null
    
    // Create new session if none selected
    if (!currentSessionId) {
      try {
        const session = await chatApi.createSession({
          jurisdiction,
          mode,
        })
        setSessions([session, ...sessions])
        currentSessionId = session.id
        navigate(`/chat/${session.id}`)
      } catch (error) {
        console.error('Failed to create session:', error)
        return
      }
    }
    
    const userMessage = input
    setInput('')
    setLoading(true)
    
    // Optimistically add user message
    setMessages(prev => [...prev, {
      id: Date.now(),
      session_id: currentSessionId!,
      role: 'user' as const,
      content: userMessage,
      sources: null,
      created_at: new Date().toISOString(),
    }])
    
    try {
      const response = await chatApi.sendMessage(currentSessionId, {
        message: userMessage,
        jurisdiction,
        mode,
      })
      
      setMessages(prev => [...prev.slice(0, -1), {
        ...prev[prev.length - 1],
        id: response.message.id - 1,
      }, response.message])
      
      // Update session in list
      loadSessions()
    } catch (error) {
      console.error('Failed to send message:', error)
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 100px)', gap: 2 }}>
      {/* Sessions sidebar */}
      <Paper sx={{ width: 280, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2 }}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<Add />}
            onClick={handleNewSession}
          >
            Новый чат
          </Button>
        </Box>
        <Divider />
        <List sx={{ flexGrow: 1, overflow: 'auto' }}>
          {sessionsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : sessions.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
              Нет чатов
            </Typography>
          ) : (
            sessions.map((session) => (
              <ListItem
                key={session.id}
                disablePadding
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => handleDeleteSession(session.id, e)}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                }
              >
                <ListItemButton
                  selected={sessionId === session.id.toString()}
                  onClick={() => navigate(`/chat/${session.id}`)}
                >
                  <ListItemText
                    primary={session.title || 'Новый чат'}
                    secondary={new Date(session.created_at).toLocaleDateString('ru-RU')}
                    primaryTypographyProps={{ noWrap: true }}
                  />
                </ListItemButton>
              </ListItem>
            ))
          )}
        </List>
      </Paper>
      
      {/* Chat area */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Settings bar */}
        <Box sx={{ p: 2, display: 'flex', gap: 2, borderBottom: 1, borderColor: 'divider' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
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
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Тип задачи</InputLabel>
            <Select
              value={mode}
              label="Тип задачи"
              onChange={(e) => setMode(e.target.value)}
            >
              {MODES.map((m) => (
                <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        
        {/* Messages */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {messages.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <SmartToy sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Начните диалог
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Задайте вопрос или выберите существующий чат
              </Typography>
            </Box>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}
          {loading && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                AI думает...
              </Typography>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>
        
        {/* Input */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Введите вопрос..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              sx={{ minWidth: 100 }}
            >
              <Send />
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  
  // Get unique document titles from sources
  const uniqueSourceTitles = message.sources 
    ? [...new Set(message.sources.map((s: SourceReference) => s.title))]
    : []
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: '80%',
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          {!isUser && (
            <SmartToy sx={{ color: 'primary.main', mt: 0.5 }} />
          )}
          <Card
            sx={{
              bgcolor: isUser ? 'primary.main' : 'grey.100',
              color: isUser ? 'white' : 'text.primary',
            }}
          >
            <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
              {isUser ? (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              ) : (
                <MarkdownContent sx={{ color: 'inherit' }}>
                  {message.content}
                </MarkdownContent>
              )}
            </CardContent>
          </Card>
          {isUser && (
            <Person sx={{ color: 'primary.main', mt: 0.5 }} />
          )}
        </Box>
        
        {/* Sources summary - visible without expanding */}
        {!isUser && uniqueSourceTitles.length > 0 && (
          <Box sx={{ ml: 4, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
              📚 Основано на:
            </Typography>
            {uniqueSourceTitles.slice(0, 3).map((title, idx) => (
              <Chip
                key={idx}
                label={title}
                size="small"
                variant="outlined"
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            ))}
            {uniqueSourceTitles.length > 3 && (
              <Typography variant="caption" color="text.secondary">
                и ещё {uniqueSourceTitles.length - 3}
              </Typography>
            )}
          </Box>
        )}
        
        {/* Expandable sources with snippets */}
        {message.sources && message.sources.length > 0 && (
          <Accordion sx={{ ml: 4 }}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="body2">
                Подробнее об источниках ({message.sources.length} фрагментов)
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {message.sources.map((source: SourceReference, idx: number) => (
                <Box key={idx} sx={{ mb: 1 }}>
                  <Chip
                    label={source.title}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mb: 0.5 }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    {source.snippet}
                  </Typography>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        )}
      </Box>
    </Box>
  )
}

