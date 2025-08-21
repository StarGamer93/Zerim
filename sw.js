// Service Worker - Enables offline functionality and caching
const CACHE_NAME = 'zerim-v1.0.0';
const STATIC_CACHE_NAME = 'zerim-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'zerim-dynamic-v1.0.0';

// Files to cache immediately (App Shell)
const STATIC_FILES = [
  '/',
  '/index.html',
  '/settings.html',
  '/analytics.html',
  '/manifest.json',
  
  // CSS Files
  '/css/main.css',
  '/css/themes.css', 
  '/css/animations.css',
  '/css/responsive.css',
  '/css/components.css',
  
  // JavaScript Files
  '/js/app.js',
  '/js/storage.js',
  '/js/settings.js',
  '/js/export.js',
  '/js/analytics.js',
  '/js/utils.js',
  '/js/categories.js',
  '/js/shortcuts.js',
  
  // Icons
  '/icons/icon-192.svg',
  '/icons/icon-512.svg',
  
  // External Dependencies
  'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

// Network-first resources
const NETWORK_FIRST = [
  '/analytics.html',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js'
];

// Cache-first resources  
const CACHE_FIRST = [
  'https://fonts.googleapis.com',
  'https://fonts.gstatic.com',
  'https://cdnjs.cloudflare.com'
];

// Install Event - Cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static files', error);
      })
  );
  
  // Force activation of new service worker
  self.skipWaiting();
});

// Activate Event - Clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE_NAME && 
              cacheName !== DYNAMIC_CACHE_NAME && 
              cacheName.startsWith('zerim-')) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Claim all clients immediately
  event.waitUntil(self.clients.claim());
});

// Fetch Event - Handle requests with different strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different types of requests with appropriate strategies
  if (isStaticFile(request.url)) {
    event.respondWith(cacheFirst(request));
  } else if (isNetworkFirst(request.url)) {
    event.respondWith(networkFirst(request));
  } else if (isCacheFirst(request.url)) {
    event.respondWith(cacheFirst(request));
  } else if (isHTMLRequest(request)) {
    event.respondWith(networkFirst(request, '/index.html'));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

// Cache First Strategy - For static assets that rarely change
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache First strategy failed:', error);
    
    // Return offline fallback if available
    if (isHTMLRequest(request)) {
      const offlinePage = await caches.match('/index.html');
      if (offlinePage) {
        return offlinePage;
      }
    }
    
    return new Response('Offline', { 
      status: 503, 
      statusText: 'Service Unavailable' 
    });
  }
}

// Network First Strategy - For dynamic content that should be fresh
async function networkFirst(request, fallbackUrl = null) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('Network failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return fallback if specified
    if (fallbackUrl) {
      const fallback = await caches.match(fallbackUrl);
      if (fallback) {
        return fallback;
      }
    }
    
    // Return offline page for HTML requests
    if (isHTMLRequest(request)) {
      const offlinePage = await caches.match('/index.html');
      if (offlinePage) {
        return offlinePage;
      }
    }
    
    return new Response('Offline', { 
      status: 503, 
      statusText: 'Service Unavailable' 
    });
  }
}

// Stale While Revalidate Strategy - For resources that should be updated when possible
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const networkRequest = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => {
    // Silently fail, we'll return cached version
  });
  
  return cachedResponse || networkRequest;
}

// Helper Functions
function isStaticFile(url) {
  return STATIC_FILES.some(file => url.includes(file));
}

function isNetworkFirst(url) {
  return NETWORK_FIRST.some(pattern => url.includes(pattern));
}

function isCacheFirst(url) {
  return CACHE_FIRST.some(pattern => url.includes(pattern));
}

function isHTMLRequest(request) {
  return request.headers.get('Accept')?.includes('text/html');
}

// Background Sync - For offline task creation
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-tasks') {
    event.waitUntil(syncTasks());
  }
});

async function syncTasks() {
  try {
    // This would sync any offline-created tasks when connection is restored
    console.log('Background sync: Syncing tasks...');
    
    // Implementation would depend on your backend API
    // For now, this is just a placeholder since we're using localStorage
    
    // Notify the main app that sync completed
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({ type: 'SYNC_COMPLETED' });
    });
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push Notifications - For task reminders
self.addEventListener('push', (event) => {
  const options = {
    body: 'You have tasks due soon!',
    icon: '/icons/icon-192.svg',
    badge: '/icons/icon-72.png',
    tag: 'task-reminder',
    data: {
      url: '/'
    },
    actions: [
      {
        action: 'view',
        title: 'View Tasks',
        icon: '/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/action-dismiss.png'
      }
    ],
    silent: false,
    requireInteraction: false
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      options.body = payload.body || options.body;
      options.data = { ...options.data, ...payload.data };
    } catch (error) {
      console.error('Failed to parse push data:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('Zerim Reminder', options)
  );
});

// Notification Click - Handle user interaction with notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const { action, data } = event;
  const url = data?.url || '/';
  
  if (action === 'dismiss') {
    return;
  }
  
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // Check if there's already a window open
      for (const client of clients) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Open new window
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});

// Message Event - Communication with main app
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'CACHE_URLS':
      event.waitUntil(cacheUrls(data.urls));
      break;
    case 'CLEAR_CACHE':
      event.waitUntil(clearCache(data.cacheName));
      break;
    case 'GET_CACHE_SIZE':
      event.waitUntil(getCacheSize().then(size => {
        event.ports[0].postMessage({ cacheSize: size });
      }));
      break;
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
  }
});

// Cache additional URLs dynamically
async function cacheUrls(urls) {
  try {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    await cache.addAll(urls);
    console.log('Service Worker: Cached additional URLs', urls);
  } catch (error) {
    console.error('Service Worker: Failed to cache URLs', error);
  }
}

// Clear specific cache
async function clearCache(cacheName) {
  try {
    const success = await caches.delete(cacheName || DYNAMIC_CACHE_NAME);
    console.log(`Service Worker: Cache ${cacheName} cleared:`, success);
    return success;
  } catch (error) {
    console.error('Service Worker: Failed to clear cache', error);
    return false;
  }
}

// Get cache size information
async function getCacheSize() {
  try {
    const cacheNames = await caches.keys();
    let totalSize = 0;
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      
      for (const request of keys) {
        const response = await cache.match(request);
        if (response) {
          const blob = await response.blob();
          totalSize += blob.size;
        }
      }
    }
    
    return {
      totalSize,
      formattedSize: formatBytes(totalSize),
      cacheCount: cacheNames.length
    };
  } catch (error) {
    console.error('Service Worker: Failed to get cache size', error);
    return { totalSize: 0, formattedSize: '0 B', cacheCount: 0 };
  }
}

// Format bytes for display
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Periodic background sync for maintenance
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'maintenance') {
    event.waitUntil(performMaintenance());
  }
});

async function performMaintenance() {
  try {
    console.log('Service Worker: Performing maintenance...');
    
    // Clean up old dynamic cache entries
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const keys = await cache.keys();
    
    // Remove entries older than 7 days
    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    
    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const dateHeader = response.headers.get('date');
        if (dateHeader) {
          const responseDate = new Date(dateHeader).getTime();
          if (responseDate < sevenDaysAgo) {
            await cache.delete(request);
            console.log('Service Worker: Removed old cache entry:', request.url);
          }
        }
      }
    }
    
    console.log('Service Worker: Maintenance completed');
  } catch (error) {
    console.error('Service Worker: Maintenance failed', error);
  }
}

// Error handling
self.addEventListener('error', (event) => {
  console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker unhandled rejection:', event.reason);
});

// Console log for debugging
console.log('Service Worker: Loaded successfully');
