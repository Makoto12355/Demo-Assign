-- Table 1: users
CREATE TABLE users (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid UNIQUE NOT NULL,
  userid text UNIQUE NOT NULL,
  email text UNIQUE NOT NULL,
  role text DEFAULT 'viewer',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Table 2: access_logs
CREATE TABLE access_logs (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES users (user_id) ON DELETE SET NULL,
  session_id text,
  path text,
  action text,
  timestamp timestamptz DEFAULT now(),
  meta jsonb DEFAULT '{}'::jsonb
);

-- Table 3: app_logs
CREATE TABLE app_logs (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp timestamptz DEFAULT now(),
    level text NOT NULL,
    logger text NOT NULL,
    message text NOT NULL,
    user_id uuid REFERENCES users (user_id) ON DELETE SET NULL,
    meta jsonb
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_access_logs_user_id ON access_logs (user_id);
CREATE INDEX idx_access_logs_timestamp ON access_logs (timestamp DESC);
CREATE INDEX idx_app_logs_timestamp ON app_logs (timestamp DESC);