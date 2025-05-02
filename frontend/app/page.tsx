"use client"

import { useState } from "react"
import Image from "next/image"
import { MessageSquare, Code, ClipboardCheck } from "lucide-react"

export default function TokenGenerator() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const [login, setLogin] = useState("")
  const [password, setPassword] = useState("")
  const [token, setToken] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setToken("")
    setIsLoading(true)

    try {
      const res = await fetch(`${API_URL}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login, password }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || "Ошибка запроса токена")
      }

      const { token: tk } = await res.json()
      setToken(tk)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Неизвестная ошибка")
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(token)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#f5f5f5]">
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-3 flex items-center">
          <Image
            src="/images/logo.png"
            alt="Company Logo"
            width={120}
            height={30}
            className="h-8 w-auto"
          />

          <nav className="hidden md:flex ml-auto space-x-6">
            <a
              href="https://webui.example.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-gray-600 hover:text-black text-sm"
            >
              <MessageSquare className="h-5 w-5 mr-2 text-violet-600" />
              Чат
            </a>
            <a
              href="https://litellm.example.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-gray-600 hover:text-black text-sm"
            >
              <Code className="h-5 w-5 mr-2 text-violet-600" />
              API
            </a>
          </nav>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-10">
        <h1 className="text-4xl font-bold text-center mb-10">Генератор токенов</h1>
        <div className="max-w-3xl mx-auto grid md:grid-cols-2 gap-8">
          {/* Form */}
          <div className="bg-white p-8 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold mb-2">Получите токен</h2>
            <p className="text-gray-600 mb-6">
              Введите логин и пароль для получения токена доступа
            </p>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label
                  htmlFor="login"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Логин:
                </label>
                <input
                  id="login"
                  type="text"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  placeholder="Имя пользователя или email"
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#C1FF05]"
                  required
                />
              </div>
              <div className="mb-6">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Пароль:
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#C1FF05]"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[#C1FF05] hover:bg-[#A8E600] text-black text-base font-medium py-3 px-4 rounded-md transition"
              >
                {isLoading ? "Загрузка..." : "Получить токен"}
              </button>
            </form>
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600">
                Ошибка: {error}
              </div>
            )}
          </div>

          {/* Token display */}
          <div>
            {token ? (
              <div className="bg-white p-8 rounded-lg shadow-sm h-full">
                <h2 className="text-2xl font-bold mb-4">Ваш токен</h2>
                <div className="bg-gray-50 px-4 py-3 rounded-md border border-gray-200 overflow-x-auto">
                  <pre className="text-sm whitespace-pre-wrap break-all">{token}</pre>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleCopy}
                    className={`w-full flex items-center justify-center text-base font-medium py-3 px-4 rounded-md transition ${
                      copied
                        ? "bg-[#C1FF05] hover:bg-[#A8E600] text-black"
                        : "bg-white border border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <ClipboardCheck className="h-5 w-5 mr-2" />
                    {copied ? "Скопировано!" : "Копировать токен"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white p-8 rounded-lg shadow-sm h-full flex flex-col justify-center items-center">
                <div className="w-24 h-24 bg-[#C1FF05] rounded-full flex items-center justify-center mb-4">
                  <svg
                    className="h-12 w-12 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-2">Безопасный доступ</h3>
                <p className="text-gray-600 text-center">
                  Токен будет отображаться здесь после успешной авторизации
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white py-6">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center">
          <Image
            src="/images/logo.png"
            alt="Company Logo"
            width={100}
            height={25}
            className="h-6 w-auto mb-4 md:mb-0"
          />
          <span className="text-sm text-gray-600">© 2025. GenAI Team</span>
        </div>
      </footer>
    </div>
  )
}
