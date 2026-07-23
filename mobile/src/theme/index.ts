import { Platform } from 'react-native';

export const Colors = {
  primary: '#9f1239', // Vinho Dehoniano
  primaryLight: '#fff1f2',
  primaryBorder: '#ffe4e6',

  background: '#FCFBF8', // Creme Papel Antigo
  white: '#FFFFFF',

  textPrimary: '#111827',
  textSecondary: '#374151',
  textTertiary: '#6b7280',
  textLight: '#9ca3af',

  border: '#e5e7eb',
  borderLight: '#f3f4f6',

  error: '#f87171',
  success: '#10b981',
};

export const Typography = {
  fontFamily: Platform.OS === 'ios' ? 'Lora' : 'serif',
  fontSize: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 24,
    xxl: 32,
  },
  fontWeight: {
    regular: '400',
    medium: '600',
    bold: '700',
    extraBold: '800',
  }
};
