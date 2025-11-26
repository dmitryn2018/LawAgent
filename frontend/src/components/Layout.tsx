import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
  Chip,
  Tooltip,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard,
  Chat,
  Description,
  Search,
  Edit,
  AdminPanelSettings,
  Logout,
  Person,
  Lock,
  Warning,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { metaApi } from '../api'
import { RuntimeInfo } from '../types'

const drawerWidth = 260

const menuItems = [
  { text: 'Главная', icon: <Dashboard />, path: '/' },
  { text: 'Чатбот', icon: <Chat />, path: '/chat' },
  { text: 'Шаблоны', icon: <Description />, path: '/templates' },
  { text: 'Проверки', icon: <Search />, path: '/due-diligence' },
  { text: 'Редактор', icon: <Edit />, path: '/editor' },
]

const adminItems = [
  { text: 'Администрирование', icon: <AdminPanelSettings />, path: '/admin' },
]

export default function Layout() {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [runtimeInfo, setRuntimeInfo] = useState<RuntimeInfo | null>(null)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const fetchRuntimeInfo = async () => {
      try {
        const info = await metaApi.getRuntime()
        setRuntimeInfo(info)
      } catch (error) {
        console.error('Failed to fetch runtime info:', error)
      }
    }
    fetchRuntimeInfo()
  }, [])

  const isLocalProvider = (provider: string) => {
    const local = ['mock', 'ollama', 'local', 'on-prem']
    return local.includes(provider.toLowerCase())
  }
  
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }
  
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }
  
  const handleMenuClose = () => {
    setAnchorEl(null)
  }
  
  const handleLogout = async () => {
    handleMenuClose()
    await logout()
    navigate('/login')
  }
  
  const handleNavigation = (path: string) => {
    navigate(path)
    if (isMobile) {
      setMobileOpen(false)
    }
  }
  
  const drawer = (
    <Box>
      <Toolbar sx={{ justifyContent: 'center' }}>
        <Typography variant="h6" noWrap component="div" color="primary" fontWeight={700}>
          Legal AI
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))}
              onClick={() => handleNavigation(item.path)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'white',
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                  '&:hover': {
                    backgroundColor: 'primary.main',
                  },
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {user?.role === 'admin' && (
        <>
          <Divider />
          <List>
            {adminItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname.startsWith(item.path)}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      color: 'white',
                      '& .MuiListItemIcon-root': {
                        color: 'white',
                      },
                    },
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  )
  
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }} />
          
          {/* Security Badge */}
          {runtimeInfo && (
            <Tooltip 
              title={`LLM: ${runtimeInfo.llm_provider}, Embeddings: ${runtimeInfo.embedding_provider}`}
            >
              <Chip
                icon={isLocalProvider(runtimeInfo.llm_provider) ? <Lock /> : <Warning />}
                label={isLocalProvider(runtimeInfo.llm_provider) ? 'AI: локальный' : 'AI: внешний'}
                size="small"
                color={isLocalProvider(runtimeInfo.llm_provider) ? 'success' : 'warning'}
                variant="outlined"
                sx={{ mr: 2 }}
              />
            </Tooltip>
          )}
          
          <IconButton onClick={handleMenuClick} sx={{ p: 0 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem disabled>
              <Person sx={{ mr: 1 }} />
              {user?.email}
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1 }} />
              Выйти
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  )
}

