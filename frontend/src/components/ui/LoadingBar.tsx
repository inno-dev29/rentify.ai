'use client';

import { useEffect } from 'react';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';

interface LoadingBarProps {
  isLoading: boolean;
  color?: string;
  height?: number;
  className?: string;
}

/**
 * A progress bar component that shows loading state
 */
export function LoadingBar({ isLoading, color = '#3b82f6', height = 3, className = '' }: LoadingBarProps) {
  // Configure NProgress
  useEffect(() => {
    // Set up NProgress configuration
    NProgress.configure({
      showSpinner: false,
      trickleSpeed: 200,
      minimum: 0.08,
      easing: 'ease',
      speed: 500,
    });

    // Add custom styles for the bar
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      #nprogress .bar {
        background: ${color} !important;
        height: ${height}px !important;
      }
    `;
    document.head.appendChild(styleElement);

    // Clean up the style element when the component unmounts
    return () => {
      document.head.removeChild(styleElement);
    };
  }, [color, height]);

  // Control the loading state
  useEffect(() => {
    if (isLoading) {
      NProgress.start();
    } else {
      NProgress.done();
    }

    // Make sure to done() on component unmount to prevent memory leaks
    return () => {
      NProgress.done();
    };
  }, [isLoading]);

  // The component doesn't render anything visible itself,
  // it just controls the NProgress bar
  return null;
}

export default LoadingBar; 