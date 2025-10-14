-- حذف الجداول إذا كانت موجودة مسبقاً
DROP TABLE IF EXISTS debug_responses;
DROP TABLE IF EXISTS debug_requests;
DROP TABLE IF EXISTS code_snippets;
DROP TABLE IF EXISTS collaboration_sessions;
DROP TABLE IF EXISTS code_files;
DROP TABLE IF EXISTS project_members;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;

-- إنشاء الجداول بشكل متكامل
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bio TEXT,
    avatar_url TEXT DEFAULT '/static/default-avatar.png',
    github_url TEXT,
    is_verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    language TEXT DEFAULT 'python',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'collaborator' CHECK(role IN ('owner', 'collaborator', 'viewer')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(project_id, user_id)
);

CREATE TABLE code_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    content TEXT DEFAULT '// Start coding here...',
    language TEXT DEFAULT 'python',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE code_snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    language TEXT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE debug_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    code_snippet TEXT,
    error_message TEXT,
    language TEXT,
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE debug_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    solution TEXT NOT NULL,
    code_fix TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upvotes INTEGER DEFAULT 0,
    is_accepted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (request_id) REFERENCES debug_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- إنشاء indexes لتحسين الأداء
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_public ON projects(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_project_members_user ON project_members(user_id);
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_code_files_project ON code_files(project_id);
CREATE INDEX idx_snippets_user ON code_snippets(user_id);
CREATE INDEX idx_snippets_public ON code_snippets(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_debug_requests_user ON debug_requests(user_id);
CREATE INDEX idx_debug_requests_status ON debug_requests(status);
CREATE INDEX idx_debug_responses_request ON debug_responses(request_id);
CREATE INDEX idx_debug_responses_accepted ON debug_responses(is_accepted) WHERE is_accepted = TRUE;
