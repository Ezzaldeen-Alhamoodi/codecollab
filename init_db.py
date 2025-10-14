import sqlite3

def init_database():
    conn = sqlite3.connect('codecollab.db')
    cursor = conn.cursor()

    # جميع الجداول التي نحتاجها
    tables = [
        # جدول المستخدمين
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bio TEXT,
            avatar_url TEXT DEFAULT '/static/default-avatar.png'
        )
        ''',

        # جدول المشاريع
        '''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            language TEXT DEFAULT 'python',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_public BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        ''',

        # جدول ملفات الكود
        '''
        CREATE TABLE IF NOT EXISTS code_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content TEXT,
            language TEXT DEFAULT 'python',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        ''',

        # جدول أعضاء المشروع (للتحديثات المستقبلية)
        '''
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'collaborator',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(project_id, user_id)
        )
        '''
    ]

    # إنشاء جميع الجداول
    for table_sql in tables:
        cursor.execute(table_sql)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")
    print("✅ Tables created: users, projects, code_files, project_members")

if __name__ == "__main__":
    init_database()
