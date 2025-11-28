import { useState } from 'react'
import { LogOut, MessageCircle } from 'lucide-react'
import AIChat from './AIChat'

interface BottomNavProps {
  onLogout: () => void
}

export default function BottomNav({ onLogout }: BottomNavProps) {
  const [showChat, setShowChat] = useState(false)

  return (
    <>
      <nav
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: '60px',
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(12px)',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          zIndex: 30,
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          padding: '0 1rem'
        }}
      >
        <button
          onClick={() => setShowChat(true)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.25rem',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.5rem 1rem',
            transition: 'opacity 0.2s ease',
            minWidth: '60px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '0.8'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '1'
          }}
        >
          <MessageCircle
            size={24}
            style={{
              color: '#60A5FA',
              strokeWidth: 1.5
            }}
          />
          <span
            style={{
              fontSize: '0.75rem',
              color: '#E6E8EB',
              fontWeight: 500,
              letterSpacing: '0.01em'
            }}
          >
            AI Chat
          </span>
        </button>

        <button
          onClick={onLogout}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.25rem',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.5rem 1rem',
            transition: 'opacity 0.2s ease',
            minWidth: '60px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '0.8'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = '1'
          }}
        >
          <LogOut
            size={24}
            style={{
              color: '#E44C65',
              strokeWidth: 1.5
            }}
          />
          <span
            style={{
              fontSize: '0.75rem',
              color: '#E6E8EB',
              fontWeight: 500,
              letterSpacing: '0.01em'
            }}
          >
            Logout
          </span>
        </button>
      </nav>

      {/* AI Chat Modal */}
      {showChat && (
        <AIChat
          onClose={() => setShowChat(false)}
          isMobile={true}
        />
      )}
    </>
  )
}
