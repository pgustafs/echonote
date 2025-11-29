import { useState } from 'react'
import { LogOut, MessageCircle, Sun, Moon } from 'lucide-react'
import AIChat from './AIChat'
import { useTheme } from '../contexts/ThemeContext'

interface BottomNavProps {
  onLogout: () => void
}

export default function BottomNav({ onLogout }: BottomNavProps) {
  const [showChat, setShowChat] = useState(false)
  const { theme, toggleTheme } = useTheme()

  return (
    <>
      <nav className="fixed bottom-0 left-0 right-0 h-[60px] bg-bg backdrop-blur-xl z-30 flex justify-around items-center px-4 bottom-nav-border">
        <button
          onClick={() => setShowChat(true)}
          className="flex flex-col items-center gap-1 bg-transparent border-none cursor-pointer p-2 min-w-[60px] hover:opacity-80 transition-opacity touch-target"
        >
          <MessageCircle
            size={24}
            className="text-ai"
            strokeWidth={2}
          />
          <span className="text-xs text-text-secondary font-medium tracking-wide">
            AI Chat
          </span>
        </button>

        <button
          onClick={toggleTheme}
          className="flex flex-col items-center gap-1 bg-transparent border-none cursor-pointer p-2 min-w-[60px] hover:opacity-80 transition-opacity touch-target"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <Sun size={24} className="text-icon" strokeWidth={2} />
          ) : (
            <Moon size={24} className="text-icon" strokeWidth={2} />
          )}
          <span className="text-xs text-text-secondary font-medium tracking-wide">
            Theme
          </span>
        </button>

        <button
          onClick={onLogout}
          className="flex flex-col items-center gap-1 bg-transparent border-none cursor-pointer p-2 min-w-[60px] hover:opacity-80 transition-opacity touch-target"
        >
          <LogOut
            size={24}
            className="text-error"
            strokeWidth={2}
          />
          <span className="text-xs text-text-secondary font-medium tracking-wide">
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
