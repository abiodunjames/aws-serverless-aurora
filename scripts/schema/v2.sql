
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER NOT NULL, 
    user_id VARCHAR(50), 
    title VARCHAR(250), 
    slug VARCHAR(20), 
    description TEXT, 
    hits INTEGER, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    UNIQUE (slug)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER NOT NULL, 
    comment_text TEXT, 
    post_id INTEGER, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(post_id) REFERENCES posts (id)
);

INSERT INTO posts (id, user_id, title, slug, description, hits) VALUES (
1, '344d117ea9f1', 'A serverless blogpost with Aurora', 'serverless-aurora', 'This is the description of the post', 0);
