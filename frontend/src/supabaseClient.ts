import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://tmblzshfpiltzxkdamdq.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYmx6c2hmcGlsdHp4a2RhbWRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczMzI2ODIsImV4cCI6MjA5MjkwODY4Mn0.5ZMTbQ5KqoQ4aEUpJtMQbE_IN44daQDmLs95fXJaseQ';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
