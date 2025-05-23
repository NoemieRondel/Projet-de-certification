CREATE DATABASE veille_ai;
USE veille_ai;
CREATE TABLE articles(
id INT auto_increment primary key,
title varchar(255),
source varchar(255),
publication_date date,
content text,
language varchar(50)
);
ALTER TABLE articles
ADD COLUMN link VARCHAR(255);

ALTER TABLE articles
ADD COLUMN author VARCHAR(255);
ALTER TABLE articles ADD CONSTRAINT unique_link UNIQUE (link);

CREATE TABLE videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    source VARCHAR(255),
    publication_date DATE,
    description TEXT,
    language VARCHAR(50),
    video_url VARCHAR(255),
    channel_id VARCHAR(255),
    channel_name VARCHAR(255),
    UNIQUE(video_url)
);
ALTER TABLE articles
ADD COLUMN keywords TEXT,
ADD COLUMN focus_tech VARCHAR(255);
ALTER TABLE videos
ADD COLUMN keywords TEXT,
ADD COLUMN focus_tech VARCHAR(255);
ALTER TABLE videos
DROP language;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM videos WHERE video_url IS NULL;
CREATE TABLE scientific_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    authors TEXT,
    publication_date DATE NOT NULL,
    abstract TEXT,
    article_url VARCHAR(1000) NOT NULL,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    keywords TEXT,
    CONSTRAINT unique_article UNIQUE (source, external_id)
);

SET SQL_SAFE_UPDATES = 0;

CREATE TABLE article_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    content LONGTEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);
ALTER TABLE article_content ADD CONSTRAINT unique_article_id UNIQUE (article_id);

ALTER TABLE articles MODIFY focus_tech varchar(1000);

ALTER TABLE videos
DROP focus_tech;

UPDATE articles
SET keywords = "";

ALTER TABLE articles
DROP focus_tech;

START TRANSACTION;

-- Renommer le champ content en summary
ALTER TABLE articles CHANGE COLUMN content summary TEXT;

-- Ajouter le champ full_content
ALTER TABLE articles ADD COLUMN full_content LONGTEXT;

-- Migrer les données
UPDATE articles a
INNER JOIN article_content ac ON a.id = ac.article_id
SET a.full_content = ac.content;

-- Supprimer la table articles_content
DROP TABLE article_content;

COMMIT;

SELECT * FROM videos ;

-- Renommer le champ content en summary
ALTER TABLE irrelevant_articles CHANGE COLUMN content summary TEXT;

-- Ajouter le champ full_content
ALTER TABLE irrelevant_articles ADD COLUMN full_content LONGTEXT;

-- Supprimer le champ focus_tech
ALTER TABLE irrelevant_articles DROP focus_tech;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  source_preferences TEXT,
  video_channel_preferences TEXT,
  keyword_preferences TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE user_preferences
ADD COLUMN alert_active BOOLEAN DEFAULT FALSE,
ADD COLUMN alert_criteria TEXT;













