import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import ChatSidebar from './ChatSidebar'

const MOBILE_SIDEBAR_QUERY = '(max-width: 900px)'

const AppShell = () => {
  const location = useLocation()
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  useEffect(() => {
    setIsMobileSidebarOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const mediaQuery = window.matchMedia(MOBILE_SIDEBAR_QUERY)
    const handleChange = (event: MediaQueryListEvent) => {
      if (!event.matches) {
        setIsMobileSidebarOpen(false)
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  useEffect(() => {
    if (!isMobileSidebarOpen) return

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMobileSidebarOpen(false)
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isMobileSidebarOpen])

  useEffect(() => {
    if (typeof document === 'undefined') return
    document.body.classList.toggle('app-shell--mobile-locked', isMobileSidebarOpen)
    return () => document.body.classList.remove('app-shell--mobile-locked')
  }, [isMobileSidebarOpen])

  const handleToggleSidebar = () => {
    setIsMobileSidebarOpen((prev) => !prev)
  }

  const handleCloseSidebar = () => {
    setIsMobileSidebarOpen(false)
  }

  return (
    <div className={`app-shell ${isMobileSidebarOpen ? 'app-shell--mobile-sidebar-open' : ''}`}>
      <Sidebar isMobileOpen={isMobileSidebarOpen} onRequestClose={handleCloseSidebar} />
      <button
        type="button"
        className="app-shell__sidebar-backdrop"
        onClick={handleCloseSidebar}
        aria-label="Close navigation menu"
      />
      <div className="app-shell__main">
        <Topbar
          onSidebarToggle={handleToggleSidebar}
          isMobileSidebarOpen={isMobileSidebarOpen}
        />
        <main className="app-shell__content">
          <Outlet />
        </main>
      </div>
      <ChatSidebar />
    </div>
  )
}

export default AppShell
