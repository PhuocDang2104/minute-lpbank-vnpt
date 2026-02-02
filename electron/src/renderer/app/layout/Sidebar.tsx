import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Home,
  Users,
  BookOpen,
  CheckSquare,
  Settings,
  LogOut,
  FolderOpen,
  FileText,
} from 'lucide-react'
import { currentUser, getInitials, actionItems } from '../../store/mockData'
import { logout, getStoredUser } from '../../lib/api/auth'
import { useLanguage } from '../../contexts/LanguageContext'

interface NavItem {
  path: string
  labelKey: string
  icon: React.ReactNode
  badge?: number
}

const overdueCount = actionItems.filter(a => a.deadline < new Date() && a.status !== 'completed').length

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const storedUser = getStoredUser()
  const displayUser = storedUser || currentUser
  const { t } = useLanguage()
  const isAdmin = (displayUser.role || '').toLowerCase() === 'admin'

  const mainNavItems: NavItem[] = [
    { path: '/app', labelKey: 'nav.dashboard', icon: <Home size={20} /> },
    { path: '/app/meetings', labelKey: 'nav.meetings', icon: <Users size={20} /> },
    { path: '/app/projects', labelKey: 'nav.projects', icon: <FolderOpen size={20} /> },
  ]

  const toolsNavItems: NavItem[] = []

  const settingsNavItems: NavItem[] = [
    { path: '/app/settings', labelKey: 'nav.settings', icon: <Settings size={20} /> },
  ]

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }
  return (
    <aside className="sidebar app-shell__sidebar">
      {/* Logo */}
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon" style={{ padding: 0, background: 'transparent' }}>
            <img
              src="/meetmate_icon.svg"
              alt="Minute"
              style={{ width: 40, height: 40, objectFit: 'contain' }}
            />
          </div>
          <span className="sidebar__logo-text">Minute</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        {/* Main Navigation */}
        <div className="sidebar__nav-section">
          <ul className="sidebar__nav-list">
            {mainNavItems.map((item) => (
              <li key={item.path} className="sidebar__nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) => {
                    const isMeetingsRoute = item.path === '/app/meetings'
                    const isMergedActive = isMeetingsRoute && (location.pathname.startsWith('/app/meetings') || location.pathname.startsWith('/app/calendar'))
                    const active = isMergedActive || (!isMeetingsRoute && isActive)
                    return `sidebar__nav-link ${active ? 'active' : ''}`
                  }}
                  end={item.path === '/app'}
                >
                  <span className="sidebar__nav-icon">{item.icon}</span>
                  <span className="sidebar__nav-label">{t(item.labelKey)}</span>
                  {item.badge && item.badge > 0 && (
                    <span className="sidebar__nav-badge">{item.badge}</span>
                  )}
                </NavLink>
              </li>
            ))}
            {toolsNavItems.map((item) => (
              <li key={item.path} className="sidebar__nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `sidebar__nav-link ${isActive ? 'active' : ''}`
                  }
                >
                  <span className="sidebar__nav-icon">{item.icon}</span>
                  <span className="sidebar__nav-label">{t(item.labelKey)}</span>
                  {item.badge && item.badge > 0 && (
                    <span className="sidebar__nav-badge">{item.badge}</span>
                  )}
                </NavLink>
              </li>
            ))}
            {settingsNavItems.map((item) => (
              <li key={item.path} className="sidebar__nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `sidebar__nav-link ${isActive ? 'active' : ''}`
                  }
                >
                  <span className="sidebar__nav-icon">{item.icon}</span>
                  <span className="sidebar__nav-label">{t(item.labelKey)}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* User Profile */}
      <div className="sidebar__footer">
        <div className="sidebar__user">
          <div className="sidebar__avatar">
            {getInitials(displayUser.display_name || displayUser.displayName || 'U')}
          </div>
          <div className="sidebar__user-info">
            <div className="sidebar__user-name">{displayUser.display_name || displayUser.displayName}</div>
            <div className="sidebar__user-role">{displayUser.role || 'User'}</div>
          </div>
          <button
            className="sidebar__logout-btn"
            onClick={handleLogout}
            title={t('nav.logout')}
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
