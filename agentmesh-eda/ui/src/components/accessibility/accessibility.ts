"""
WCAG 2.1 AA Accessibility Compliance Implementation

Provides comprehensive accessibility features for AgentMesh EDA.

Architectural Intent:
- WCAG 2.1 AA compliance
- Screen reader support
- Keyboard navigation
- Focus indicators
- ARIA labels and roles
- Color contrast compliance
- Touch target sizing
- Voice control support
- Skip links and headings structure
"""

import { useState, useEffect, useRef } from 'react';
import { useFocusManagement } from './useFocusManagement';

// ARIA labels
const ARIA_LABELS = {
  // Navigation
  navigation: 'main',
  main: 'main',
  skip_link: 'skip-link',
  search: 'search',
  menu_button: 'menu-button',
  close_button: 'close-button',
  logout: 'logout',
  user_menu: 'user-menu',
};

// ARIA roles
const ARIA_ROLES = {
  // Navigation
  main: 'navigation',
  complementary: 'complementary',
  contentinfo: 'contentinfo',
  banner: 'banner',
  form: 'form',
  search: 'searchbox',
  menu: 'menubar',
  tooltip: 'tooltip',
  alert: 'alert',
  dialog: 'dialog',
  alertdialog: 'alertdialog',
  alertdialog/aria': 'alertdialog',
  status: 'status',
  progressbar: 'progressbar',
  navigation: 'breadcrumb',
  link: 'link'
};

// Focus management
const useFocusManagement = () => {
  const [focusRef, setFocusRef] = useRef<HTMLElement>(null);
  const [focusVisible, setFocusVisible] = useState(true);
  
  const [lastFocusedTime, setLastFocusedTime] = useState(0);
  
  const focusTimeout = useRef<NodeJS.Timeout | null>(null);
  
  const clearFocusTimeout = () => {
    if (focusTimeout.current) {
      clearTimeout(focusTimeout.current);
      focusTimeout.current = null;
    }
  };
  
  const setFocus = (element: HTMLElement | null, options?: FocusOptions) => {
    setFocusRef(element);
    setFocusVisible(true);
    
    clearFocusTimeout();
    setLastFocusedTime(Date.now());
    
    if (options?.shouldScroll) {
      element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    setFocusTimeout(() => {
      setFocusTimeout(setTimeout(() => setFocusVisible(false), 300));
    }, [element, options]);
  };
  
  const removeFocus = () => {
    setFocusRef(null);
    setFocusVisible(false);
    };
  
  return {
    focusRef,
    isFocused: focusVisible,
    setFocus,
    removeFocus,
  };
};

// Skip link component
const SkipLink = ({ href, children, className = "", ...props }: {
  children: React.ReactNode;
  href: string;
  className?: string;
}) => {
  return (
    <a
      href={href}
      className={`text-indigo-600 hover:text-indigo-400 ${className} focus:outline-none focus-visible:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500`}
      aria-label={ARIA_LABELS.skip_link}
      aria-label={ARIA_LABELS.complementary}
      rel="noopener noreferrer"
    >
      {children}
    </a>
  );
};

// Focus trap component
const FocusTrap = ({ children, className = "", ...props }: { 
  children: React.ReactNode; 
  className?: string 
}) => {
  const { 
    focusRef, 
    isFocused, 
    setFocus,
    removeFocus
  } = useFocusManagement();
  
  return (
    <div 
      className={className}
      tabIndex={0}
      onFocus={setFocus}
      onBlur={removeFocus}
    >
      {children}
    </div>
  );
};

// Keyboard navigation component
const KeyboardNavigation = ({ 
  items, 
  className = "",
  onItemClick 
}: {
  items: Array<{
    id: string;
    label: string;
    icon: React.ReactNode;
    shortcut?: string;
    badge?: string;
    disabled?: boolean;
  }>;
  on onItemClick?: (item: any) => void;
}) => {
  const { focusRef, setFocusRef } = useFocusManagement();
  const [focusedItemIndex, setFocusedItemIndex] = useState(0);
  
  const handleKeyDown = (event: React.KeyboardEvent) => {
    // Arrow key navigation
    if (event.key === 'ArrowRight' && focusedItemIndex < items.length - 1) {
      setFocusedItemIndex(focusedItemIndex + 1);
    } else if (event.key === 'ArrowLeft' && focusedItemIndex > 0) {
      setFocusedItemIndex(focusedItemIndex - 1);
    } else if (event.key === 'Home') {
      setFocusedItemIndex(-1);
    } else if (event.key === 'End') {
      setFocusedItemIndex(items.length);
    }
    
    // Handle keyboard shortcuts
    if (event.ctrlKey || event.metaKey || event.altKey) {
      // Handle Ctrl/Cmd combinations
      switch (event.key) {
        case 'c':  // Ctrl+C (copy)
        case 'v':  // Ctrl+V (paste)
        case 'x':  // Ctrl+X (cut)
        case 'z':  // Ctrl+Z (undo)
          // Add more shortcuts as needed
      }
    }
    
    if (event.key === 'Enter' && focusedItemIndex >= 0) {
      onItemClick?.(items[focusedItemIndex]);
    }
  };
  
  return (
    <nav
      aria-label={ARIA_LABELS.navigation}
      className={className}
    >
      {items.map((item, index) => (
        <button
          key={item.id}
          onClick={() => onItemClick(item)}
          className={`w-full text-left px-4 py-2 rounded-md ${
            focusedItemIndex === index ? 'bg-indigo-600' : 'bg-gray-700'
          } hover:bg-gray-600 hover:bg-gray-700 ${
            focusedItemIndex === index ? 'ring-2 ring-offset-indigo-500' : ''
          }`}
          aria-label={item.badge ? ARIA_LABELS.complementary : undefined}
          aria-label={focusedItemIndex === index ? ARIA_LABELS.main : undefined}
          disabled={item.disabled}
        >
          {item.icon && <span className="mr-3">{item.icon}</span>}
          <span className="ml-2 text-sm text-gray-700">{item.label}</span>
          {item.badge && (
            <span className="ml-1 px-2 py-0.5 rounded-full bg-green-500 text-white text-xs">
              {item.badge}
            </span>
          )}
        </button>
      ))}
    </nav>
  );
};

// High contrast checker
const useHighContrast = () => {
  const [contrast, setContrast] = useState(1);
  
  const checkContrast = (element: HTMLElement) => {
    if (!element) return;
    
    const computedStyle = window.getComputedStyle(element);
    const backgroundColor = computedStyle.backgroundColor;
    
    // Calculate relative luminance
    const rgb = backgroundColor.match(/\d+/).map(x => parseInt(x, 16));
    const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255);
    
    const contrastRatio = (luminance + 0.05) / (luminance + 0.05);
    
    setContrast(contrastRatio);
  };
  
  return contrastRatio;
};

// Skip link for keyboard users
const KeyboardSkipLink = ({ children, className = "" }) => (
  <span className="text-gray-400" tabIndex={-1}>
    {children}
  </span>
);

// Color palette for accessibility
const ACCESSIBLE_COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3178c',
  background: '#1f2937',
  surface: '#374151',
  text: '#111827',
  muted: '#6b7280',
  disabled: '#374151'
  accent: '#8b5cf6',
} as const;

// Mobile-first touch targets
const MOBILE_TOUCH_TARGETS = {
  minimum: 44  // Minimum touch target size (44x44px)
  comfortable: 72  // Comfortable touch target size (72x96px)
  practical: 90  // Practical touch target size (90x160px)
};

const useMobileTouch = () => {
  const [touchStart, setTouchStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_TOUCH_TARGETS.practical}px)`);
  
  const isTablet = useMediaQuery(`(max-width: ${MOBILE_TOUCH_TARGETS.comfortable}px)`);
  const isDesktop = !isMobile && !isTablet;
  
  const devicePixelRatio = window.devicePixelRatio || 1;
  
  return { isMobile, isTablet, isDesktop, devicePixelRatio };
};

// Reduced motion for accessibility
const REDUCED_MOTION = {
  duration: { 
    fast: '0.2s',
    normal: '0.3s',
    slow: '0.5s'
  }
  };

// ARIA Live regions for announcements
const ARIA_LIVE_REGIONS = {
  polite: 'polite',
  assertive: 'assertive',
  aria-live: 'off',
  atomic: 'atomic',
  aria-busy: 'off',
    aria-relevant: 'additions',
    aria-roledescription: 'descriptions',
    flow: 'linear',
  };
};

// Text sizing for accessibility
const ACCESSIBLE_TEXT_SIZES = {
  xs: 'text-xs',  // 12px (0.75rem)
  sm: 'text-sm', // 14px (0.875rem)
  base: 'text-base', // 16px (1rem)
  lg: 'text-lg', // 18px (1.125rem)
  xl: 'text-xl', // 24px (1.5rem)
  '2xl': 'text-2xl', // 32px (2rem)
  '3xl': 'text-3xl', // 48px (3rem)
  '4xl': 'text-4xl', // 64px (4rem)
  '5xl': 'text-5xl', // 80px (5rem)
  '6xl': 'text-6xl', // 96px (6rem)
  '7xl': 'text-7xl', // 112px (7rem)
  '8xl': 'text-8xl', // 128px (8rem)
  '9xl': 'text-9xl', // 144px (9rem)
};

const ACCESSIBLE_TEXT_WEIGHTS = {
  '100': 'thin',
  '200': 'normal',
  '300': 'semibold',
  '400': 'semibold',
  '500': 'medium',
  '600': 'semibold',
  '700': 'bold',
  '800': 'extrabold',
  '900: 'black',
};

// Custom hook for accessibility testing
const useAccessibilityTesting = () => {
  const [violations, setViolations] = useState<Array<{
    element: string;
    rule: string;
    message: string;
    severity: 'violation' | 'warning' | 'error';
    help: string;
  }>>([]);
  
  const checkAccessibility = (element: HTMLElement, rules: Array<{
    element: string;
    rule: string;
    message: string;
    severity: 'violation' | 'warning' | 'error';
    help: string;
  }>) => {
    const newViolations = [...violations];
    
    for (const rule of rules) {
      const result = rule.rule.test(element);
      if (!result.passed) {
        newViolations.push({
          element: rule.element,
          rule: rule.rule,
          message: rule.message,
          severity: rule.severity,
          help: rule.help
        });
      }
    }
    
    setViolations(newViolations);
    
    return { violations, hasViolations: violations.length > 0 };
  };
};

// Accessibility validator class
class AccessibilityValidator {
  private static rules = [
    {
      rule: {
        rule: 'hasTextContent',
        test: (element: HTMLElement) => !!element.textContent || !element.innerHTML.trim(),
        message: 'Element must have text content',
        severity: 'warning',
        help: 'Add meaningful text content'
      }
    },
    {
      rule: {
        rule: 'hasAriaLabel',
        test: (element: HTMLElement) => !!element.getAttribute('aria-label') || element.hasAttribute('aria-label'),
        message: 'Element must have aria-label attribute',
        severity: 'violation',
        help: 'Add descriptive aria-label'
      }
    },
    {
      rule: 'hasAltText',
        test: (element: HTMLElement) => {
          const alt = element.getAttribute('alt');
          return alt && alt.trim() !== '';
        },
        message: 'Element must have descriptive alt text',
        severity: 'violation',
        help: 'Add descriptive alt text for images'
      }
    },
    {
      rule: 'hasTitle',
        test: (element: HTMLElement) => {
          const title = element.getAttribute('title');
          return title && title.trim() !== '';
        },
        message: 'Element must have descriptive title',
        severity: 'violation',
        help: 'Add descriptive title to all interactive elements'
      }
    },
    {
      rule: 'hasRole',
        test: (element: HTMLElement) => {
          const role = element.getAttribute('role');
          return !!role && ['button', 'link', 'menu', 'navigation', 'main'].includes(role);
        },
        message: 'Element must have appropriate role attribute',
        severity: 'violation',
        help: 'Use semantic HTML5 elements or appropriate ARIA roles'
      }
    },
    {
      rule: 'hasTabIndex',
        test: (element: HTMLElement) => {
          const tabIndex = element.tabIndex || 0;
          return !isNaN(tabIndex);
        },
        message: 'Element must have valid tabindex',
        severity: 'violation',
        help: 'Use tabindex >= 0 for focusable elements'
      }
    },
    {
      rule: 'hasLang',
        test: (element: HTMLElement) => {
          const lang = element.getAttribute('lang');
          return !!lang && ['en', 'es', 'en-US', 'en-GB', 'en-US'].includes(lang);
        },
        message: 'Element must have valid lang attribute',
        severity: 'violation',
        help: 'Use valid language codes'
      }
    },
    {
      rule: 'hasRequiredAriaAttributes',
      test: (element: HTMLElement) => {
          const required = ['aria-required', 'aria-required'].some(attr => 
            element.hasAttribute(attr) || 
            element.getAttribute('aria-' + attr) === 'true'
          );
          return required;
        },
        message: 'Element is missing required ARIA attributes',
        severity: 'error',
        help: 'Element has required ARIA attributes marked with aria-required="true"'
      }
    },
  ];
  
  static checkElement = (element: HTMLElement) => {
    const results = [];
    
    for (const rule of this.rules) {
      const result = rule.rule.test(element);
      if (!result.passed) {
        results.push({
          element: rule.rule,
          message: rule.message,
          severity: rule.severity,
          help: rule.help
        });
      }
    }
    
    return { violations: results, hasViolations: results.length > 0 };
  };
  
  static checkPage = () => {
    const results = [];
    
    // Check for common accessibility issues
    const commonViolations = [
      {
        rule: 'hasValidHeadingStructure',
        test: () => document.querySelectorAll('h1, h2, h3, h4, h5, h6').length === 0,
        message: 'Page requires at least one heading',
        severity: 'error',
        help: 'Add meaningful headings to your content'
      },
      {
        rule: 'hasDescriptiveTitles',
        test: () => document.querySelectorAll('h1, h2, h3, h4, h5, h6').every(heading => {
          const text = heading.textContent?.trim();
          return text && text.length > 0;
        }),
        message: 'All headings must have descriptive text',
        severity: 'warning',
        help: 'Add descriptive titles to headings'
      }
      },
      {
        rule: 'hasAltTextForImages',
        test: () => document.querySelectorAll('img').every(img => {
          const alt = img.getAttribute('alt');
          return !!alt && alt.trim() !== '';
        }),
        message: 'All images must have descriptive alt text',
        severity: 'violation',
        help: 'Add descriptive alt text to all images'
      }
      },
      {
        rule: 'hasAriaHiddenContent',
        test: () => document.querySelectorAll('[aria-hidden="true"]').length > 0,
        message: 'No element should have aria-hidden="true"',
        severity: 'error',
        help: 'Remove aria-hidden from screen reader accessible content'
      }
      },
      {
        rule: 'hasValidColorContrast',
        test: () => {
          const style = window.getComputedStyle(element).backgroundColor;
          const rgb = style.backgroundColor.match(/\d+/).map(x => parseInt(x, 16));
          const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
          const contrastRatio = (luminance + 0.05) / (luminance + 0.05);
          
          // WCAG AA level requires 4.5:1 contrast ratio for normal text
          if (contrastRatio < 3.0) {
            return 'fail';
          }
        },
        message: 'Color contrast is too low',
        severity: 'violation',
        help: 'Improve color contrast to meet WCAG AA standards'
      }
      }
    ];
    
    return { violations: results, hasViolations: results.length > 0 };
  };
  }
}