import { createContext, useContext, useRef, useState } from 'react'
import type { ReactNode } from 'react'

interface ToastContextValue {
  toast: string | null
  setToast: (message: string) => void
}

export const ToastContext = createContext<ToastContextValue>({
  toast: null,
  setToast: () => {},
})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToastState] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function setToast(message: string) {
    if (timerRef.current !== null) clearTimeout(timerRef.current)
    setToastState(message)
    timerRef.current = setTimeout(() => {
      setToastState(null)
      timerRef.current = null
    }, 3400)
  }

  return (
    <ToastContext.Provider value={{ toast, setToast }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext)
}
