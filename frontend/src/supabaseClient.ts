import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://tmblzshfpiltzxkdamdq.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYmx6c2hmcGlsdHp4a2RhbWRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczMzI2ODIsImV4cCI6MjA5MjkwODY4Mn0.5ZMTbQ5KqoQ4aEUpJtMQbE_IN44daQDmLs95fXJaseQ';

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Supabase credentials not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
