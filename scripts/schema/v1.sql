

CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL, 
    user_id VARCHAR(50) NOT NULL, 
    email VARCHAR(65), 
    PRIMARY KEY (id), 
    UNIQUE (email)
);
