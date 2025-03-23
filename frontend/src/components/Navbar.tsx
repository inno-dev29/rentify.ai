'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/app/context/AuthContext';

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      setIsMenuOpen(false);
      
      // Redirect to home page after logout
      router.push('/');
      router.refresh();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-primary">rentify.ai</span>
            </Link>
            <div className="hidden md:ml-6 md:flex md:space-x-8">
              <Link 
                href="/" 
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  pathname === '/' 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-secondary hover:border-gray-300 hover:text-primary'
                }`}
              >
                Home
              </Link>
              <Link 
                href="/properties" 
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  pathname === '/properties' 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-secondary hover:border-gray-300 hover:text-primary'
                }`}
              >
                Properties
              </Link>
              {isAuthenticated && (
                <>
                  <Link 
                    href="/recommendations/conversational" 
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      pathname === '/recommendations/conversational' 
                        ? 'border-primary text-primary' 
                        : 'border-transparent text-secondary hover:border-gray-300 hover:text-primary'
                    }`}
                  >
                    AI Recommendations
                  </Link>
                  <Link 
                    href="/bookings" 
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      pathname === '/bookings' 
                        ? 'border-primary text-primary' 
                        : 'border-transparent text-secondary hover:border-gray-300 hover:text-primary'
                    }`}
                  >
                    My Bookings
                  </Link>
                  <Link 
                    href="/image-hosting-guide" 
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      pathname === '/image-hosting-guide' 
                        ? 'border-primary text-primary' 
                        : 'border-transparent text-secondary hover:border-gray-300 hover:text-primary'
                    }`}
                  >
                    Image Guide
                  </Link>
                </>
              )}
            </div>
          </div>
          
          <div className="hidden md:ml-6 md:flex md:items-center">
            {isAuthenticated ? (
              <div className="ml-3 relative group">
                <div>
                  <button
                    type="button"
                    className="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    id="user-menu-button"
                    onClick={toggleMenu}
                  >
                    <span className="sr-only">Open user menu</span>
                    <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                  </button>
                </div>
                {isMenuOpen && (
                  <div
                    className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
                    role="menu"
                    aria-orientation="vertical"
                    aria-labelledby="user-menu-button"
                  >
                    <div className="px-4 py-2 text-xs text-gray-500">
                      Signed in as <span className="font-semibold">{user?.username}</span>
                    </div>
                    <Link
                      href="/profile"
                      className="block px-4 py-2 text-sm text-secondary hover:bg-gray-100"
                      role="menuitem"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      Your Profile
                    </Link>
                    {user?.is_staff && (
                      <Link
                        href="/admin"
                        className="block px-4 py-2 text-sm text-secondary hover:bg-gray-100"
                        role="menuitem"
                        onClick={() => setIsMenuOpen(false)}
                      >
                        Admin Dashboard
                      </Link>
                    )}
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-secondary hover:bg-gray-100"
                      role="menuitem"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex space-x-4">
                <Link
                  href="/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary bg-white hover:bg-gray-50"
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-blue-700"
                >
                  Sign up
                </Link>
              </div>
            )}
          </div>
          
          {/* Mobile menu button */}
          <div className="-mr-2 flex items-center md:hidden">
            <button
              onClick={toggleMenu}
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu, show/hide based on menu state */}
      <div className={`${isMenuOpen ? 'block' : 'hidden'} md:hidden`}>
        <div className="pt-2 pb-3 space-y-1">
          <Link
            href="/"
            className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
              pathname === '/'
                ? 'bg-blue-50 border-primary text-primary'
                : 'border-transparent text-secondary hover:bg-gray-50 hover:border-gray-300 hover:text-primary'
            }`}
            onClick={() => setIsMenuOpen(false)}
          >
            Home
          </Link>
          <Link
            href="/properties"
            className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
              pathname === '/properties'
                ? 'bg-blue-50 border-primary text-primary'
                : 'border-transparent text-secondary hover:bg-gray-50 hover:border-gray-300 hover:text-primary'
            }`}
            onClick={() => setIsMenuOpen(false)}
          >
            Properties
          </Link>
          {isAuthenticated && (
            <>
              <Link
                href="/recommendations/conversational"
                className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                  pathname === '/recommendations/conversational'
                    ? 'bg-blue-50 border-primary text-primary'
                    : 'border-transparent text-secondary hover:bg-gray-50 hover:border-gray-300 hover:text-primary'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                AI Recommendations
              </Link>
              <Link
                href="/bookings"
                className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                  pathname === '/bookings'
                    ? 'bg-blue-50 border-primary text-primary'
                    : 'border-transparent text-secondary hover:bg-gray-50 hover:border-gray-300 hover:text-primary'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                My Bookings
              </Link>
              <Link
                href="/image-hosting-guide"
                className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                  pathname === '/image-hosting-guide'
                    ? 'bg-blue-50 border-primary text-primary'
                    : 'border-transparent text-secondary hover:bg-gray-50 hover:border-gray-300 hover:text-primary'
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                Image Guide
              </Link>
            </>
          )}
        </div>
        
        <div className="pt-4 pb-3 border-t border-gray-200">
          {isAuthenticated ? (
            <>
              <div className="flex items-center px-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-secondary">{user?.username}</div>
                </div>
              </div>
              <div className="mt-3 space-y-1">
                <Link
                  href="/profile"
                  className="block px-4 py-2 text-base font-medium text-secondary hover:text-primary hover:bg-gray-100"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Your Profile
                </Link>
                {user?.is_staff && (
                  <Link
                    href="/admin"
                    className="block px-4 py-2 text-base font-medium text-secondary hover:text-primary hover:bg-gray-100"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Admin Dashboard
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2 text-base font-medium text-secondary hover:text-primary hover:bg-gray-100"
                >
                  Sign out
                </button>
              </div>
            </>
          ) : (
            <div className="mt-3 space-y-1 px-2">
              <Link
                href="/login"
                className="block px-3 py-2 rounded-md text-base font-medium text-secondary hover:text-primary hover:bg-gray-50"
                onClick={() => setIsMenuOpen(false)}
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="block px-3 py-2 rounded-md text-base font-medium text-secondary hover:text-primary hover:bg-gray-50"
                onClick={() => setIsMenuOpen(false)}
              >
                Sign up
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
} 