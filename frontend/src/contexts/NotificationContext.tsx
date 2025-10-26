import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Notification {
  id: string;
  type: 'task' | 'approval' | 'message' | 'system';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  priority?: 'high' | 'medium' | 'low';
  navigateTo?: string;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  deleteNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const initialNotifications: Notification[] = [
  {
    id: '1',
    type: 'approval',
    title: 'New approval needed',
    message: 'AI-generated response for Sarah Johnson is ready for review',
    timestamp: '5 minutes ago',
    read: false,
    priority: 'high',
    navigateTo: '/approval',
  },
  {
    id: '2',
    type: 'task',
    title: 'Task completed',
    message: 'Records request for Mike Chen has been processed',
    timestamp: '1 hour ago',
    read: false,
    navigateTo: '/',
  },
  {
    id: '3',
    type: 'message',
    title: 'New client message',
    message: 'David Martinez sent a follow-up question',
    timestamp: '2 hours ago',
    read: true,
    navigateTo: '/inbox',
  },
  {
    id: '4',
    type: 'system',
    title: 'System update',
    message: 'AI agents performance improved by 15%',
    timestamp: '1 day ago',
    read: true,
    navigateTo: '/agents',
  },
];

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>(initialNotifications);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        clearAll,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
