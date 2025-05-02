import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Генератор токенов",
  description: "Получите токен доступа для использования API LiteLLM",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}
