-- Désactiver temporairement les contraintes de clé étrangère pour faciliter la suppression des tables
SET FOREIGN_KEY_CHECKS = 0;

-- Supprimer les tables si elles existent déjà, dans l'ordre inverse des dépendances
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS videos;
DROP TABLE IF EXISTS scientific_articles;
DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS monitoring_logs; 

-- Réactiver les contraintes de clé étrangère
SET FOREIGN_KEY_CHECKS = 1;


-- Création de la table 'users'
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table 'articles'
CREATE TABLE articles (
  id INT AUTO_INCREMENT primary key,
  title varchar(255),
  source varchar(255),
  publication_date date,
  summary text,
  language varchar(50),
  link VARCHAR(255),
  author VARCHAR(255),
  keywords TEXT,
  full_content LONGTEXT,
  CONSTRAINT unique_link UNIQUE (link)
);

-- Création de la table 'videos'
CREATE TABLE videos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255),
  source VARCHAR(255),
  publication_date DATE,
  description TEXT,
  video_url VARCHAR(255),
  channel_id VARCHAR(255),
  channel_name VARCHAR(255),
  keywords TEXT,
  UNIQUE(video_url)
);

-- Création de la table 'scientific_articles'
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

-- Création de la table 'user_preferences'
CREATE TABLE user_preferences (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  source_preferences TEXT,
  video_channel_preferences TEXT,
  keyword_preferences TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Création de la table 'password_reset_tokens'
CREATE TABLE password_reset_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Création de la table 'monitoring_logs'
CREATE TABLE monitoring_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  script VARCHAR(100) NOT NULL,
  duration_seconds FLOAT,

  -- Champs pour articles "classiques"
  articles_count INT,
  empty_full_content_count INT,
  average_keywords_per_article FLOAT,
  summaries_generated INT,
  average_summary_word_count FLOAT,

  -- Champs pour articles scientifiques
  scientific_articles_count INT,
  empty_abstracts_count INT,
  average_keywords_per_scientific_article FLOAT
);

-- Insertion d'un utilisateur de test
INSERT INTO users (username, email, password_hash)
VALUES ('testuser', 'test@example.com', 'hashed_password');

-- Insertion d'un article
INSERT INTO articles (
  title, source, publication_date, summary, language,
  link, author, keywords, full_content
)
VALUES (
  'AI Revolution in 2025',
  'Wired',
  '2025-04-20',
  'A brief summary about AI trends in 2025.',
  'en',
  'https://wired.com/ai-revolution-2025',
  'Jane Doe',
  'AI;Technology;2025',
  'Full content about AI revolution...'
);

-- Insertion d'une vidéo
INSERT INTO videos (
  title, source, publication_date, description, video_url,
  channel_id, channel_name, keywords
)
VALUES (
  'Understanding Generative AI',
  'YouTube',
  '2025-04-19',
  'An explanation of generative AI in 2025.',
  'https://youtube.com/watch?v=genai2025',
  'channel_123',
  'AI Channel',
  'Generative AI;Deep Learning;Trends'
);

-- Insertion d’un article scientifique
INSERT INTO scientific_articles (
  title, authors, publication_date, abstract, article_url,
  source, external_id, keywords
)
VALUES (
  'A Study on RAG for Knowledge Intensive Tasks',
  'Alice Smith; John Roe',
  '2025-04-10',
  'This paper explores Retrieval-Augmented Generation (RAG) for QA.',
  'https://arxiv.org/abs/2504.12345',
  'arXiv',
  '2504.12345',
  'RAG;QA;NLP'
);

-- Insertion d’un log de monitoring
INSERT INTO monitoring_logs (
  timestamp, script, duration_seconds,
  articles_count, empty_full_content_count, average_keywords_per_article,
  summaries_generated, average_summary_word_count,
  scientific_articles_count, empty_abstracts_count, average_keywords_per_scientific_article
)
VALUES (
  NOW(), 'daily_fetch.py', 12.5,
  10, 1, 3.2,
  9, 120.0,
  3, 0, 2.7
);

-- Insertion de préférences utilisateur
INSERT INTO user_preferences (
  user_id, source_preferences, video_channel_preferences, keyword_preferences
)
VALUES (
  1, 'Wired;VentureBeat', 'AI Channel;ML Today', 'AI;Deep Learning;NLP'
);