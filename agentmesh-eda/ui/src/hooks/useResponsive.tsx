"""
Responsive Design and Mobile Optimization

Ensures AgentMesh UI works seamlessly across all devices and viewports.

Architectual Intent:
- Mobile-first responsive design
- Progressive enhancement for larger screens
- Touch-friendly interaction patterns
- Performance optimization for mobile devices
- Accessibility-first responsive design
- Flexible grid and layout systems
- Optimized images and assets
"""

import { useState, useEffect } from 'react'
import { useBreakpoint, useMediaQuery } from '@mui/material'

// Breakpoint configuration
const breakpoints = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
  xxl: 1920,
}

// Responsive hook
export const useResponsive = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery('(max-width: 600px)');
  const isTablet = useMediaQuery('(max-width: 900px) and (min-width: 601px)');
  const isDesktop = useMediaQuery('(min-width: 1200px)');

  return {
    theme,
    isMobile,
    isTablet,
    isDesktop,
  };
};

// Hook for optimized images
export const useOptimizedImage = (src: string, options: any = {}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(src);
  const [error, setError] = useState(null);

  useEffect(() => {
    const img = new Image();
    
    img.onload = () => {
      setIsLoaded(true);
      setError(null);
    };
    
    img.onerror = () => {
      setError(`Failed to load image: ${src}`);
    };
    
    img.src = currentSrc;
    setCurrentSrc(currentSrc);
    
    // Set image attributes for optimization
    img.loading = 'lazy';
    img.decoding = 'async';
    img.sizes = '(max-width: 1920px) 100vw';
    
  }, [currentSrc, isLoaded, error]);
};

// Responsive grid component
interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  spacing?: number;
  columns?: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
}

const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  className = '',
  spacing = 4,
  columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 6, xxl: 12 },
}) => {
  const { theme } = useTheme();
  const isMobile = useMediaQuery('(max-width: 600px)');
  const isTablet = useMediaQuery('(max-width: 900px) and (min-width: 601px)');
  const isDesktop = useMediaQuery('(min-width: 1200px)');

  const getGridClassName = () => {
    if (isDesktop) {
      return `grid-cols-${columns.xl} ${className}`;
    } else if (isTablet) {
      return `grid-cols-${columns.md} ${className}`;
    } else if (isMobile) {
      return `grid-cols-${columns.sm} ${className}`;
    } else {
      return `grid-cols-${columns.xs} ${className}`;
    }
  };

  return (
    <div className={`${getGridClassName()} gap-${spacing}`}>
      {children}
    </div>
  );
};

// Mobile navigation component
const MobileNavigation = ({ isOpen, onToggle }: { isOpen: boolean; onToggle: () => void }) => {
  return (
    <div 
      className={`fixed bottom-0 left-0 right-0 z-50 transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-y-0' : 'translate-y-full'
      }`}
    >
      <div className="flex items-center justify-between h-16 px-4 bg-gray-800 border-t border-gray-700">
        <div className="flex items-center">
          <LayoutDashboard className="w-5 h-5 text-indigo-500" />
          <span className="ml-3 text-white text-sm font-medium">AgentMesh</span>
        </div>
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800 rounded-md p-1"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>
    </div>

      <nav className={`${isOpen ? 'block' : 'hidden'}`}>
        <div className="px-4 py-2 space-y-1">
          <a
            href="/"
            className="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-200"
          >
            <Home className="w-5 h-5 mr-3" />
            <span className="text-gray-700">Dashboard</span>
          </a>
          
          <a
            href="/agents"
            className="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-200"
          >
            <Users className="w-5 h-5 mr-3" />
            <span className="text-gray-700">Agents</span>
          </a>
          
          <a
            href="/tasks"
            className="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-200"
          >
            <Briefcase className="w-5 h-5 mr-3" />
            <span className="text-gray-700">Tasks</span>
          </a>
          
          <a
            href="/metrics"
            className="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors duration-200"
          >
            <BarChart2 className="w-5 h-5 mr-3" />
            <span className="text-gray-700">Metrics</span>
          </a>
          
          <a
            href="/settings"
            className="flex items-center px-3 py-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors-200"
          >
            <Settings className="w-5 h-5 mr-3" />
            <span className="text-gray-700">Settings</span>
          </a>
        </div>

        <div className="border-t border-gray-700 pt-4 pb-2">
          <div className="px-4">
            <div className="text-xs text-gray-400 text-center mb-2">Quick Actions</div>
            <div className="grid grid-cols-4 gap-2">
              <button className="bg-gray-700 hover:bg-gray-600 p-3 rounded-lg text-white">
                <Zap className="w-4 h-4" />
                <span>Create Agent</span>
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 p-3 rounded-lg text-white">
                <Upload className="w-4 h-4" />
                <span>Import</span>
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 p-3 rounded-lg text-white">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </nav>
    </div>
  );
};

// Touch-optimized card component
const TouchOptimizedCard = ({ 
  children, 
  className = "",
  onClick,
  hover = false 
}: {
  const theme = useTheme();
  const [isPressed, setIsPressed] = useState(false);
  const [ripples, setRipples] = useState<Array<{ id: string; x: number; y: number; size: number }>>([]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    
    const ripple = {
      id: `ripple-${Date.now()}-${Math.random()}`,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      size: Math.max(rect.width, rect.height),
      color: theme.palette.primary.main,
    };
    
    setRipples(prev => [...prev, ripple]);
    setIsPressed(true);
  };

  const handleMouseUp = () => {
    setIsPressed(false);
    setTimeout(() => setRipples([]), 600);
  };

  return (
    <div
      className={`relative bg-gray-800 rounded-lg p-6 transition-all duration-200 ${
        hover ? 'transform -translate-y-1 shadow-lg border-indigo-500' : ''
      } ${
        pressed ? 'scale-95 shadow-2xl' : ''
      }`}
      onClick={onClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="relative overflow-hidden rounded-lg">
        <div className="absolute inset-0 rounded-lg overflow-hidden">
          <div className={`h-full w-full rounded-lg bg-gray-900 ${className}`}>
            {children}
          </div>
        </div>
        
        {ripples.map(ripple => (
          <span
            key={ripple.id}
            className={`absolute rounded-full bg-indigo-500 opacity-75 animate-ping pointer-events-none`}
            style={{
              left: ripple.x,
              top: ripple.y,
              width: ripple.size,
              height: ripple.size,
              transform: 'translate(-50%, -50%)',
            }}
          />
        ))}
      </div>
    </div>
  );
};

// Optimized performance component
const OptimizedList = ({ items, className = "", itemHeight = 80 }: {
  items: React.ReactNode[];
  className?: string;
  itemHeight?: number;
}) => {
  const [visibleItems, setVisibleItems] = useState(items.slice(0, 10));
  const [scrollIndex, setScrollIndex] = useState(0);
  
  const handleScroll = (e: React.UIEvent) => {
    const scrollTop = e.currentTarget.scrollTop;
    const clientHeight = e.currentTarget.clientHeight;
    const maxScroll = clientHeight - (e.currentTarget as HTMLElement).scrollHeight;
    
    const index = Math.round((scrollTop / (maxScroll - clientHeight)) * (items.length - visibleItems.length));
    
    setVisibleItems(prev => [
      ...prev.slice(index, index + 10),
      ...prev.slice(index + 10, index + 20)
    ]);
    setScrollIndex(index);
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="relative overflow-y-auto" style={{ height: `${itemHeight * Math.min(items.length, 10)}` }}>
        <div style={{
          transform: `translateY(-${scrollIndex * itemHeight}px)`,
        }}>
          {visibleItems.map((item, index) => (
            <div
              key={`${item}-${index}`}
              className="flex items-center"
            >
              {item}
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex justify-center mt-4">
        <button
          onClick={() => {
            const nextIndex = Math.min(scrollIndex + 1, items.length - visibleItems.length);
            setScrollIndex(nextIndex);
          }}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// Mobile charts
const MobileChartContainer = ({ title, children, height = 300 }: { 
  title: string; 
  children: React.ReactNode; 
  height: number 
}) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 h-full">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      <div className="relative h-full">
        {children}
      </div>
    </div>
  );
};

// Touch gesture hook
export const useSwipeGestures = () => {
  const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(null);
  const [touchEnd, setTouchEnd] = useState<{ x: number; y: number } | null>(null);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | 'up' | 'down' | null>(null);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart({ x: e.touches[0].clientX, y: e.touches[0].clientY });
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (touchStart) {
      const deltaX = e.touches[0].clientX - touchStart.x;
      const deltaY = e.touches[0].clientY - touchStart.y;
      setSwipeDirection(
        Math.abs(deltaX) > Math.abs(deltaY) ? 'right' : 
        Math.abs(deltaX) < Math.abs(deltaY) ? 'left' : 'up'
      );
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    setTouchEnd({ x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY });
    setSwipeDirection(null);
    setTouchStart(null);
  };

  return {
    touchStart,
    touchEnd,
    swipeDirection,
  };
};

// Touch-friendly component
const TouchableCard = ({ children, onTouchEnd, className = "", ...props }: {
  children: React.ReactNode;
  onTouchEnd?: (event: React.TouchEvent) => void;
  className?: string;
}) => {
  const [isPressed, setIsPressed] = useState(false);
  
  const handleTouchStart = () => {
    setIsPressed(true);
  };

  const handleTouchEnd = () => {
    setIsPressed(false);
    };

  return (
    <div
      className={`${className} ${isPressed ? 'scale-95' : 'scale-100'} touch-manipulation-none`}
      onTouchStart={handleTouchStart}
      onTouchEnd={onTouchEnd}
      style={{
        WebkitTapHighlightColor: 'rgba(59, 130, 246, 0.1)',
      WebkitTapHighlightColor: 'rgba(59, 130, 246, 0.1)',
      WebkitUserSelect: 'none',
      WebkitTouchCallout: 'none',
      userSelect: 'none',
        WebkitUserDrag: 'none',
        WebkitUserModify: 'none',
        WebkitUserResize: 'none',
        cursor: 'pointer',
      }}
    >
      {children}
    </div>
  );
};

// Keyboard navigation hook
export const useKeyboardNavigation = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery('(max-width: 600px)');
  
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Tab') {
      event.preventDefault();
    }
    
    // Keyboard shortcuts for mobile
    if (event.key === 'Escape') {
      // Handle escape for overlays
    }
    
    // Navigation shortcuts
    if (event.ctrlKey && event.key === 'k') {
      // Handle Ctrl+K for main menu
    }
  };
  
  return {
    handleKeyDown,
    isMobile,
    theme,
  };
};

// Loading states with skeleton screens
const MobileSkeleton = ({ className = "" }: { className?: string }) => {
  return (
    <div className={`animate-pulse ${className} bg-gray-800 rounded-lg p-4`}>
      <div className="flex items-center space-x-4">
        <div className="w-3 h-3 bg-gray-700 rounded-full animate-pulse" />
        <div className="w-3 h-3 bg-gray-700 rounded-full animate-pulse" />
        <div className="w-3 h-3 bg-gray-700 rounded-full animate-pulse" />
      </div>
    </div>
  );
};

// Pull-to-refresh component
const PullToRefresh = ({ onRefresh, isRefreshing = false }: { 
  onRefresh: () => void; 
  isRefreshing?: boolean 
}) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [isPulling, setIsPulling] = useState(false);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setPulling(true);
      const startY = e.touches[0].clientY;
      setPullDistance(0);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isPulling) {
      const currentY = e.touches[0].clientY;
      const newDistance = currentY - startY;
      setPullDistance(Math.max(0, newDistance));
    }
  };

  const handleTouchEnd = () => {
    if (pullDistance > 50) {
      // Trigger refresh if pulled far enough
      onRefresh();
    }
    setIsPulling(false);
    setPullDistance(0);
  };

  return (
    <div className="flex flex-col items-center justify-center h-32">
      <div className={`mb-4 ${isRefreshing ? 'animate-spin' : ''}`}>
        <div className="w-8 h-8 border-2 border-gray-600 rounded-full" />
      </div>
      
      <div className="text-sm text-gray-500 text-center">
        {isRefreshing ? 'Refreshing...' : 'Pull down to refresh'}
      </div>
      
      {!isRefreshing && (
        <button
          onClick={onRefresh}
          className="bg-indigo-600 text-white rounded-md p-3 hover:bg-indigo-700 touch-manipulation-none"
        >
          <RefreshCw className="w-4 h-4" />
          <span className="ml-2">Refresh</span>
        </button>
      )}
    </div>
  );
};

// Mobile-optimized form component
const MobileForm = ({ 
  children, 
  className = "", 
  onSubmit, 
  ...props 
}: {
  children: React.ReactNode;
  className?: string;
  onSubmit?: (data: any) => void;
}) => {
  const theme = useTheme();
  const [focused, setFocused] = useState<string | null>(null);
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const validateField = (name: string, value: string, rules: Array<{ required?: boolean; pattern?: RegExp; message?: string }>) => {
    for (const rule of rules) {
      if (rule.required && !value.trim()) {
        return { field: name, valid: false, message: `${name} is required` };
      }
      
      if (rule.pattern && !rule.pattern.test(value)) {
        return { field: name, valid: false, message: `${name} is invalid format` };
      }
      
      return { field: name, valid: true, message: null };
    };

  const handleSubmit = (data: any) => {
    const newErrors: Record<string, string> = {};
    let isValid = true;
    
    // Validate form fields
    Object.keys(data).forEach(field => {
      const validation = validateField(field, data[field]);
      if (!validation.valid) {
        newErrors[field] = validation.message;
        isValid = false;
      }
    });
    
    setErrors(newErrors);
    
    if (isValid && onSubmit) {
      onSubmit(data);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`space-y-4 ${className} bg-gray-800 rounded-lg p-6`}
      noValidate
    >
      {children}
      
      {Object.entries(errors).map(([field, error]) => (
        <div key={field} className="text-red-500 text-sm">
          {error}
        </div>
      ))}
    </form>
  );
};

// Scroll utilities
const useInfiniteScroll = (hasMore: boolean, callback?: () => void, threshold = 1000) => {
  const [isFetching, setIsFetching] = useState(false);
  
  const handleScroll = () => {
    if (!hasMore && !isFetching) {
      setIsFetching(true);
      
      // Simulate loading more content
      if (callback) {
        callback();
      }
    }
  };
  
  return { isFetching, handleScroll };
};

const useSmoothScroll = (element: React.RefObject<HTMLElement>) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const handleScroll = () => {
    const elementTop = element.scrollTop ? element.getBoundingClientRect().top : 0;
    const currentScrollTop = element.scrollTop;
    
    setScrollTop(currentScrollTop);
    
    // Smooth scroll to new position
    if (element.scrollTo) {
      element.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth',
      });
    }
  };
  
  return { scrollTop, handleScroll };
};

// Device detection utilities
export const useDeviceDetect = () => {
  const [device, setDevice] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  
  useEffect(() => {
    const userAgent = navigator.userAgent;
    
    if (/Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)) {
      setDevice('mobile');
    } else if (/Tablet|iPad|Android(?!.*Mobile)|IEMobile/i.test(userAgent)) {
      setDevice('tablet');
    } else {
      setDevice('desktop');
    }
  }, []);
  
  return { device, isMobile, isTablet, isDesktop };
};

// Network status hook
export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
  }, [isOnline]);
  
  return { isOnline, isOnline };
};