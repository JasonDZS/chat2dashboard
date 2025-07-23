import { createContext, useContext, useState, useEffect } from 'react'

const BackendContext = createContext()

// eslint-disable-next-line react-refresh/only-export-components
export const useBackend = () => {
  const context = useContext(BackendContext)
  if (!context) {
    throw new Error('useBackend must be used within a BackendProvider')
  }
  return context
}

export const BackendProvider = ({ children }) => {
  const [backendUrl, setBackendUrl] = useState('')

  useEffect(() => {
    // Load backend URL from localStorage on mount
    const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000'
    setBackendUrl(savedUrl)

    // Listen for backend URL changes from Settings page
    const handleBackendUrlChange = (event) => {
      setBackendUrl(event.detail.url)
    }

    window.addEventListener('backendUrlChanged', handleBackendUrlChange)

    return () => {
      window.removeEventListener('backendUrlChanged', handleBackendUrlChange)
    }
  }, [])

  const updateBackendUrl = (url) => {
    setBackendUrl(url)
    localStorage.setItem('backendUrl', url)
    window.dispatchEvent(new CustomEvent('backendUrlChanged', { 
      detail: { url } 
    }))
  }

  const value = {
    backendUrl,
    updateBackendUrl
  }

  return (
    <BackendContext.Provider value={value}>
      {children}
    </BackendContext.Provider>
  )
}