import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Navbar from '@/components/Navbar'
import { AuthProvider } from './context/AuthContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'rentify.ai',
  description: 'Find your perfect rental property',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <Navbar />
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-gray-100 mt-12 py-6">
            <div className="container mx-auto px-4 text-center text-gray-500">
              <p>© {new Date().getFullYear()} rentify.ai. All rights reserved.</p>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  )
}
