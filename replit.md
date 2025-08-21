# Overview

Zerim is a feature-rich, offline-first Progressive Web Application (PWA) designed for advanced task management and productivity tracking. The application provides a comprehensive to-do list experience with analytics, customizable themes, keyboard shortcuts, categories, and data export/import capabilities. Built with vanilla JavaScript and modern web APIs, it focuses on performance, accessibility, and offline functionality through service worker implementation.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Single Page Application (SPA)**: Built with vanilla JavaScript using ES6 modules for clean code organization
- **Progressive Web App (PWA)**: Includes manifest.json and service worker for offline functionality and app-like experience
- **Modular JavaScript Architecture**: Organized into distinct modules (app.js, storage.js, analytics.js, settings.js, etc.) for maintainability
- **CSS Architecture**: Modular CSS with separate files for main styles, themes, animations, responsive design, and components
- **Component-Based UI**: Reusable UI components with consistent styling patterns

## Data Storage
- **Client-Side Storage**: Uses localStorage for persistent data storage without requiring a backend
- **Storage Manager**: Centralized storage operations through a dedicated Storage class
- **Data Structure**: JSON-based task storage with support for categories, priorities, due dates, and completion status
- **Analytics Storage**: Separate storage for tracking productivity metrics and usage statistics
- **Settings Storage**: Persistent user preferences and configuration data

## PWA Implementation
- **Service Worker**: Implements caching strategies for offline functionality
- **Cache Management**: Separates static assets, dynamic content, and API responses
- **Offline-First Design**: Application works fully offline with data synchronization capabilities
- **App Installation**: Supports installation on mobile and desktop platforms

## Theme System
- **CSS Custom Properties**: Dynamic theming using CSS variables
- **Multiple Themes**: Support for default, dark, and other custom themes
- **Theme Persistence**: User theme preferences saved and restored across sessions

## Feature Architecture
- **Task Management**: Full CRUD operations with categories, priorities, due dates, and subtasks
- **Analytics Engine**: Comprehensive productivity tracking with charts and statistics
- **Export/Import System**: Support for JSON and CSV data formats
- **Keyboard Shortcuts**: Extensive hotkey support for power users
- **Search and Filtering**: Real-time search with multiple filter options
- **Responsive Design**: Mobile-first approach with adaptive layouts

# External Dependencies

## CSS and UI Libraries
- **Google Fonts**: Poppins font family for typography
- **Font Awesome**: Icon library for UI elements (version 6.4.0)

## JavaScript Libraries
- **Chart.js**: Data visualization library for analytics charts and graphs
- **date-fns**: Date manipulation and formatting library for analytics

## Browser APIs
- **Service Worker API**: For offline functionality and background sync
- **Web App Manifest**: For PWA installation and app metadata
- **LocalStorage API**: For client-side data persistence
- **Notification API**: For task reminders and alerts
- **File API**: For data import/export functionality

## Development Tools
- **ES6 Modules**: Native JavaScript modules for code organization
- **CSS Grid and Flexbox**: Modern CSS layout systems for responsive design
- **CSS Custom Properties**: For dynamic theming and styling